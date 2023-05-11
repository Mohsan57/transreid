from email_validator import validate_email, EmailNotValidError
from hashing import hash
import schemas, db_models
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import os

def add_new_user(db,name, email, password):
        is_new_account = True # False for login pages
        try:
            validation = validate_email(email=email, check_deliverability=is_new_account)
            
            email = validation.email
        
            
            password = hash.get_password_hash(password)
            new_user = db_models.User(name = name, email = email, password = password)
        
            try:
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user_id = new_user.id
                directory = str(user_id)
                # Parent Directory path
                parent_dir = "users/"
                # Path
                path = os.path.join(parent_dir, directory)
                os.mkdir(path)
                return new_user
            except IntegrityError as i:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This Email is already Register")
        except EmailNotValidError as e:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Email is Invalid")

def show_user_data(db,form_data):
    current_user_email = form_data.email
    user = db.query(db_models.User).filter(db_models.User.email == current_user_email).first()
    return user
