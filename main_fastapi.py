from fastapi import FastAPI
import joblib
import pandas as pd
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


# Load model
model = joblib.load("credit_risk_model.pkl")

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# Input data
class CreditRisk(BaseModel):
    person_age: int
    person_income: int
    person_emp_length: float
    loan_amnt: int
    loan_int_rate: float
    loan_percent_income: float
    cb_person_cred_hist_length: int
    person_home_ownership: str
    loan_grade: str
    cb_person_default_on_file: str
    loan_intent: str

class PredictionResponse(BaseModel):
    loan_status: int    


# Home page
@app.get("/")
def home():
    return {"message": "Credit Risk Prediction API is running"}


# Prediction
@app.post("/predict",response_model=PredictionResponse)
def predict(data: CreditRisk):

    input_row = pd.DataFrame([{
        "person_age": data.person_age,
        "person_income": data.person_income,
        "person_home_ownership": data.person_home_ownership,
        "person_emp_length": data.person_emp_length,
        "loan_intent": data.loan_intent,
        "loan_grade": data.loan_grade,
        "loan_amnt": data.loan_amnt,
        "loan_int_rate": data.loan_int_rate,
        "loan_percent_income": data.loan_percent_income,
        "cb_person_default_on_file": data.cb_person_default_on_file,
        "cb_person_cred_hist_length": data.cb_person_cred_hist_length
    }])

    prediction = model.predict(input_row)

    return PredictionResponse(
        loan_status=int(prediction[0])
    )