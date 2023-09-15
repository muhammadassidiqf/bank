import json
import random
import string
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


def load_data():
    with open('bank_data.json', 'r') as file:
        existing_data = json.load(file)
    return existing_data


def save_data(data):
    with open('bank_data.json', 'w') as file:
        json.dump(data, file, indent=4)


class TransactionModel(BaseModel):
    nominal: int
    no_rekening: str


class RegistrationModel(BaseModel):
    nama: str
    nik: str
    no_hp: str


def gen_rekening(length=10):
    account_chars = ''.join(random.choice(string.digits)
                            for _ in range(length))
    return account_chars


@app.post("/daftar", response_model=dict)
async def daftar(reg_data: RegistrationModel):
    data = load_data()
    nik = [a.get('nik') for a in data['data']]
    no_hp = [a.get('no_hp') for a in data['data']]
    if reg_data.nik in nik or reg_data.no_hp in no_hp:
        raise HTTPException(status_code=400, detail="Data already exists")

    no_rekening = gen_rekening()
    new_data = {
        **reg_data.dict(),
        "no_rekening": no_rekening,
        "tabungan": 0,
        "mutasi": []
    }

    data['data'].append(new_data)

    save_data(data)

    return {"message": "Registration successful", "no_rekening": no_rekening}


@app.post("/tabung", response_model=dict)
async def tabung(tabung_data: TransactionModel):
    data = load_data()
    data_account = [a.get('no_rekening') for a in data['data']]
    if tabung_data.no_rekening not in data_account:
        raise HTTPException(status_code=400, detail="Data not already exists")

    date_today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_data = {
        **tabung_data.dict(),
        "kode_transaksi": "C",
        "waktu": date_today
    }
    saldo = None
    for a in data['data']:
        if tabung_data.no_rekening == a.get('no_rekening'):
            a['tabungan'] = a.get('tabungan') + int(tabung_data.nominal)
            a['mutasi'].append(new_data)
            saldo = a['tabungan']

    save_data(data)

    return {"message": "Transaction successful", "saldo": saldo}


@app.post("/tarik", response_model=dict)
async def tarik(tarik_data: TransactionModel):
    data = load_data()
    data_account = [a.get('no_rekening') for a in data['data']]
    if tarik_data.no_rekening not in data_account:
        raise HTTPException(status_code=400, detail="Data not already exists")

    date_today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_data = {
        **tarik_data.dict(),
        "kode_transaksi": "D",
        "waktu": date_today
    }
    saldo = None
    for a in data['data']:
        if tarik_data.no_rekening == a.get('no_rekening'):
            a['tabungan'] = a.get('tabungan') - int(tarik_data.nominal)
            a['mutasi'].append(new_data)
            saldo = a['tabungan']

    save_data(data)

    return {"message": "Transaction successful", "saldo": saldo}


@app.post("/saldo/{no_rekening}", response_model=dict)
async def saldo(no_rekening: str):
    data = load_data()
    data_account = [a for a in data['data']
                    if no_rekening == a.get('no_rekening')]
    if len(data_account) == 0:
        raise HTTPException(status_code=400, detail="Data not already exists")

    return {"message": "Transaction successful", "saldo": data_account[0]['tabungan']}


@app.post("/mutasi/{no_rekening}", response_model=dict)
async def mutasi(no_rekening: str):
    data = load_data()
    data_account = [a for a in data['data']
                    if no_rekening == a.get('no_rekening')]
    if len(data_account) == 0:
        raise HTTPException(status_code=400, detail="Data not already exists")

    return {"message": "Transaction successful", "mutasi": data_account[0]['mutasi']}
