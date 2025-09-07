from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from neo4j import GraphDatabase
from passlib.context import CryptContext
from typing import List
import jwt, datetime, uuid

# ========== CONFIG ==========
SECRET_KEY = "mysecret"
ALGORITHM = "HS256"

app = FastAPI()
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="signin")

# CORS cho frontend HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== MODELS ==========
class UserSignup(BaseModel):
    username: str
    password: str

class Product(BaseModel):
    name: str
    description: str
    price: float
    location: str

class CartAction(BaseModel):
    product_id: str

# ========== UTILS ==========
def create_access_token(data: dict, expires_delta: int = 60):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_user_from_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ========== AUTH ==========
@app.post("/signup")
def signup(user: UserSignup):
    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {username:$username}) RETURN u", 
            username=user.username
        )
        if result.single():
            raise HTTPException(status_code=400, detail="Username already exists")

        user_id = str(uuid.uuid4())
        hashed_pw = get_password_hash(user.password)
        session.run(
            "CREATE (u:User {id:$id, username:$username, password:$password})",
            id=user_id, username=user.username, password=hashed_pw
        )
        return {"msg": "Signup successful"}

@app.post("/signin")
def signin(form_data: OAuth2PasswordRequestForm = Depends()):
    with driver.session() as session:
        result = session.run(
            "MATCH (u:User {username:$username}) RETURN u",
            username=form_data.username
        ).single()
        if not result:
            raise HTTPException(status_code=400, detail="Invalid username or password")

        user = result["u"]
        if not verify_password(form_data.password, user["password"]):
            raise HTTPException(status_code=400, detail="Invalid username or password")

        token = create_access_token({"sub": user["id"]})
        return {"access_token": token, "token_type": "bearer"}

# ========== PRODUCTS ==========
@app.post("/products")
def create_product(product: Product, user_id: str = Depends(get_user_from_token)):
    product_id = str(uuid.uuid4())
    with driver.session() as session:
        session.run(
            """
            MATCH (u:User {id:$user_id})
            CREATE (p:Product {id:$pid, name:$name, description:$desc, price:$price, location:$loc})
            CREATE (u)-[:POSTED]->(p)
            """,
            user_id=user_id, pid=product_id, name=product.name, desc=product.description, price=product.price, loc=product.location
        )
    return {"msg": "Product created", "id": product_id}

@app.get("/products/search")
def search_products(q: str = "", location: str = ""):
    query = "MATCH (p:Product) WHERE p.name CONTAINS $q "
    params = {"q": q}
    if location:
        query += "AND p.location = $location "
        params["location"] = location
    query += "RETURN p"

    with driver.session() as session:
        result = session.run(query, **params)
        products = [dict(record["p"]) for record in result]
    return products

# ========== CART ==========
@app.post("/cart/add")
def add_to_cart(item: CartAction, user_id: str = Depends(get_user_from_token)):
    with driver.session() as session:
        session.run(
            """
            MATCH (u:User {id:$uid}), (p:Product {id:$pid})
            MERGE (u)-[:ADDED_TO_CART]->(p)
            """,
            uid=user_id, pid=item.product_id
        )
    return {"msg": "Product added to cart"}

@app.get("/cart")
def view_cart(user_id: str = Depends(get_user_from_token)):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {id:$uid})-[:ADDED_TO_CART]->(p:Product)
            RETURN p
            """,
            uid=user_id
        )
        return [dict(record["p"]) for record in result]

@app.post("/cart/checkout")
def checkout(user_id: str = Depends(get_user_from_token)):
    with driver.session() as session:
        session.run(
            """
            MATCH (u:User {id:$uid})-[r:ADDED_TO_CART]->(p:Product)
            DELETE r
            """,
            uid=user_id
        )
    return {"msg": "Checkout successful"}
