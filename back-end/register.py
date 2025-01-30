from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from config import User, get_session, UserCreate, CreateAccountRequest, Compte
from utils import generate_iban, hash_password

router = APIRouter()

@router.post("/register", response_model=dict)
async def create_user(user: UserCreate, session: Session = Depends(get_session)):
    try:
        existing_user = session.exec(select(User).where(User.email == user.email)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="E-mail déjà utilisé.")

        if len(user.password) < 8:
            raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères.")

        hashed_password = hash_password(user.password)

        new_user = User(email=user.email, password=hashed_password)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        iban_account = generate_iban()
        while session.exec(select(Compte).where(Compte.iban_account == iban_account)).first():
            iban_account = generate_iban()

        is_first_account = session.exec(select(Compte).where(Compte.user_id == new_user.id)).first() is None
        account_name = "Compte principal" if is_first_account else "Compte sans nom"
        money_value = 100 if is_first_account else 0  # Vous pouvez définir une valeur par défaut ici

        new_account = Compte(user_id=new_user.id, money_value=money_value, iban_account=iban_account, account_name=account_name, first=True)
        session.add(new_account)
        session.commit()
        session.refresh(new_account)

        return {"email": new_user.email, "iban": new_account.iban_account, "account_name": new_account.account_name, "message": "Compte ouvert avec succès"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        raise HTTPException(status_code=400, detail="E-mail déjà utilisé.")
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères.")

