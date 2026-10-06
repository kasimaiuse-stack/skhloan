import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split,StratifiedKFold,cross_validate
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score



df=pd.read_csv('credit_risk_dataset.csv')

## EDA

# print(df.head())
# print(df.shape)
# print(df.isnull().sum())
# print(df.duplicated().sum())
# print(df.info())
# print(df['loan_status'].unique())
# print(df['loan_status'].value_counts())
# sns.countplot(x='loan_status',data=df)
# plt.show()
# print(df.describe())
# numerical_col=df.select_dtypes(include=np.number).columns # here selecting only numerical(float64 and int64) columns
# print(numerical_col)

# for i in numerical_col:#one by one creating graph of each numerical columns
#     sns.boxplot(x=df[i])
#     plt.show()

# print((df['person_age']))
# print((df['person_age']>100).sum())#here we find max age .which age is greater than 100

# print((df['person_emp_length']) )
# print((df['person_emp_length']>60).sum())#we find emp_length greater than 60        

# sns.heatmap(df.corr(numeric_only=True),annot=True)#correlation cheacking of numeric columns only
# plt.show()

## Remove dulicates row 
  
# print(f'orignal row:{df.shape[0]}')
df.drop_duplicates(inplace=True)
# print(f'remove row:{df.shape[0]}')

# print(df.shape)

df=df[(df['person_age']>=18) & (df['person_age']<=100)] # removeing age which is below 18 and above 100


df=df[(df['person_emp_length'] <=df['person_age']) & (df['person_emp_length'] <=60)]# removeing emp_length(exprience of employee) which is greater than there age or greater than 60
# print(df.shape)

df=df[(df['loan_amnt'] >0 )]#keep those record which loa amount is greater than zero

#Train_test_split model and using pipline

X=df.drop(['loan_status'], axis=1)
y=df['loan_status']

X_train, X_test, y_train, y_test = train_test_split( X, y, test_size=0.2, random_state=42,stratify=y)#stratify=y meaning is here we have 1 & 0 in y the equale amount of 1 and 0 goes into train and test 

numerical_col=['person_age','person_income','person_emp_length','loan_amnt','loan_int_rate','loan_percent_income','cb_person_cred_hist_length']
categarical_col=['person_home_ownership','loan_grade','cb_person_default_on_file','loan_intent']

#find class weigth

neg,pos=np.bincount(y_train)
scale_weigth=neg/pos#here we see neg class(Zero) is 3.63 time higher than pos class(One)...3.63 is class weigth
#print(scale_weigth)

##creat piplien and columnstransformer

#logistic Regression
preprocessor_lr = ColumnTransformer(
    transformers=[
        #numerical columns&pipline
        ('num',
        Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]),
        numerical_col),# Syntext of columnstransfomer (name_of_transfomer,pipline_name,columns_name)
        #catagerical columns&pipline
        ('cat',Pipeline([
            ('imputer', SimpleImputer(fill_value='Missing', strategy='constant')),
            ('one_hot', OneHotEncoder(handle_unknown='ignore'))
    ]),categarical_col) 
    ]
)

#XGBoost

preprocessor_xg = ColumnTransformer(
    transformers=[
        #numerical columns&pipline
        ('num',
        Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            
        ]),
        numerical_col),# Syntext of columnstransfomer (name_of_transfomer,pipline_name,columns_name)
        #catagerical columns&pipline
        ('cat',Pipeline([
            ('imputer', SimpleImputer(fill_value='Missing', strategy='constant')),
            ('one_hot', OneHotEncoder(handle_unknown='ignore'))
    ]),categarical_col) 
    ]
)

##crosse validation (folding)

cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
scoring={'roc_auc':'roc_auc','accuracy':'accuracy','precision':'precision','recall':'recall','f1':'f1'}

#logistic regrssion model
lr_cv_pipline=Pipeline([
    ('preprocesser',preprocessor_lr),
    ('classifier',LogisticRegression(random_state=42,max_iter=1000,class_weight='balanced'))
])

#XGBoost Model

xgb_cv_pipeline = Pipeline([
    ('preprocessor', preprocessor_xg),
    ('classifier', XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.1,
        scale_pos_weight=scale_weigth,
        random_state=42
        
    ))
])

#train model

for cv_name,pipe in [('Logistic Regression',lr_cv_pipline),('XGBoost',xgb_cv_pipeline)]:
    cv_result=cross_validate(pipe,X_train,y_train,cv=cv,scoring=scoring,n_jobs=-1)
    # print("\n", cv_name)
    # print("ROC-AUC:", cv_result['test_roc_auc'].mean())
    # print("Accuracy:", cv_result['test_accuracy'].mean())
    # print("Precision:", cv_result['test_precision'].mean())
    # print("Recall:", cv_result['test_recall'].mean())
    # print("F1:", cv_result['test_f1'].mean())

#select XGboost model
xgb_cv_pipeline.fit(X_train, y_train)
xgb_preds = xgb_cv_pipeline.predict(X_test)

accuracy = accuracy_score(y_test, xgb_preds)
precision = precision_score(y_test, xgb_preds)
recall = recall_score(y_test, xgb_preds)
f1 = f1_score(y_test, xgb_preds)

xgb_probs = xgb_cv_pipeline.predict_proba(X_test)[:, 1]
roc_auc = roc_auc_score(y_test, xgb_probs)

# print("XGBoost Test Results" )
# print("ROC-AUC:", roc_auc)
# print("Accuracy:", accuracy)
# print("Precision:", precision)
# print("Recall:", recall)
# print("F1:", f1)

joblib.dump(xgb_cv_pipeline, "credit_risk_model.pkl")
print("Model saved successfully!")