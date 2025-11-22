"""
Flask API for User Authentication and AI Chat
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import hash_password, verify_password, create_token, token_required, admin_required, decode_token
from database import users_collection, chats_collection
from datetime import datetime
from bson import ObjectId
import logging

# Import AI components
from agents.simple_chart_parser import ChartParser
from agents.smart_orchestrator import SmartOrchestrator
from agents.gemini_embeddings import GeminiEmbeddings
from agents.openrouter_synthesizer import OpenRouterSynthesizer
from agents.question_complexity import QuestionComplexityClassifier
import config
import os

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

# Initialize AI components
chart_parser = None
smart_orchestrator = None

def init_ai():
    global chart_parser, smart_orchestrator
    try:
        chart_parser = ChartParser()
        
        if config.USE_REAL_RAG:
            from agents.real_rag_retriever import RealRAGRetriever as RAGRetriever
        else:
            from agents.vector_search_retriever import VectorSearchRetriever as RAGRetriever
        
        rag_retriever = RAGRetriever(
            project_id=config.PROJECT_ID,
            location=config.REGION,
            corpus_id=config.CORPUS_ID,
            top_k=config.RAG_TOP_K,
            similarity_threshold=config.RAG_SIMILARITY_THRESHOLD
        )
        
        synthesizer = OpenRouterSynthesizer(
            api_key=os.getenv("OPENROUTER_API_KEY", "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"),
            model_name="openai/gpt-4.1-mini",
            temperature=0.6,
            max_output_tokens=2000,
        )
        
        embedder = GeminiEmbeddings(
            project_id=config.PROJECT_ID,
            location=config.REGION,
            model="text-embedding-004",
            dimension=768
        )
        
        smart_orchestrator = SmartOrchestrator(
            embedder=embedder,
            rag_retriever=rag_retriever,
            synthesizer=synthesizer,
            syn_retriever=None,
            classifier=QuestionComplexityClassifier(),
        )
        logger.info("✅ AI components initialized")
    except Exception as e:
        logger.error(f"AI init failed: {e}")

# ===== AUTH ENDPOINTS =====

@app.route("/auth/login", methods=["POST", "OPTIONS"])
def auth_login():
    if request.method == "OPTIONS":
        return "", 200
    return login()

@app.route("/auth/signup", methods=["POST", "OPTIONS"])
def auth_signup():
    if request.method == "OPTIONS":
        return "", 200
    return signup()

@app.route("/auth/me", methods=["GET", "OPTIONS"])
def auth_me():
    if request.method == "OPTIONS":
        return "", 200
    
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Token missing"}), 401
    
    try:
        token_str = token.split(" ")[1]
        data = decode_token(token_str)
        request.user = data
    except Exception as e:
        return jsonify({"error": f"Invalid token: {str(e)}"}), 401
    
    return get_profile()

@app.route("/auth/verify", methods=["POST", "OPTIONS"])
def verify_token_endpoint():
    if request.method == "OPTIONS":
        return "", 200
    
    data = request.json
    token = data.get("token")
    
    if not token:
        return jsonify({"error": "Token required"}), 400
    
    try:
        decoded = decode_token(token)
        return jsonify({"valid": True, "user": decoded}), 200
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401

@app.route("/api/signup", methods=["POST", "OPTIONS"])
def signup():
    if request.method == "OPTIONS":
        return "", 200
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400
    
    user = {
        "email": email,
        "password": hash_password(password),
        "name": name,
        "is_admin": False,
        "created_at": datetime.utcnow(),
        "active": True
    }
    
    result = users_collection.insert_one(user)
    token = create_token(str(result.inserted_id), email, False)
    
    return jsonify({
        "message": "User created",
        "token": token,
        "user": {"id": str(result.inserted_id), "email": email, "name": name}
    }), 201

@app.route("/api/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200
    data = request.json
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    user = users_collection.find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    
    if not user.get("active", True):
        return jsonify({"error": "Account disabled"}), 403
    
    token = create_token(str(user["_id"]), email, user.get("is_admin", False))
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "email": email,
            "name": user.get("name", ""),
            "is_admin": user.get("is_admin", False)
        }
    }), 200

@app.route("/api/me", methods=["GET"])
@token_required
def get_profile():
    user = users_collection.find_one({"_id": ObjectId(request.user["user_id"])})
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name", ""),
        "is_admin": user.get("is_admin", False),
        "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
    }), 200

# ===== ADMIN ENDPOINTS =====

@app.route("/api/admin/users", methods=["GET"])
@token_required
@admin_required
def get_all_users():
    users = list(users_collection.find())
    return jsonify([{
        "id": str(u["_id"]),
        "email": u["email"],
        "name": u.get("name", ""),
        "is_admin": u.get("is_admin", False),
        "active": u.get("active", True),
        "created_at": u.get("created_at").isoformat() if u.get("created_at") else None
    } for u in users]), 200

@app.route("/api/admin/users/<user_id>", methods=["GET"])
@token_required
@admin_required
def get_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name", ""),
        "password": user["password"],
        "is_admin": user.get("is_admin", False),
        "active": user.get("active", True),
        "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
    }), 200

@app.route("/api/admin/users", methods=["POST"])
@token_required
@admin_required
def create_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400
    
    user = {
        "email": email,
        "password": hash_password(password),
        "name": data.get("name", ""),
        "is_admin": data.get("is_admin", False),
        "active": data.get("active", True),
        "created_at": datetime.utcnow()
    }
    
    result = users_collection.insert_one(user)
    return jsonify({"message": "User created", "id": str(result.inserted_id)}), 201

@app.route("/api/admin/users/<user_id>", methods=["PUT"])
@token_required
@admin_required
def update_user(user_id):
    data = request.json
    update_fields = {}
    
    if "name" in data:
        update_fields["name"] = data["name"]
    if "email" in data:
        update_fields["email"] = data["email"]
    if "password" in data:
        update_fields["password"] = hash_password(data["password"])
    if "is_admin" in data:
        update_fields["is_admin"] = data["is_admin"]
    if "active" in data:
        update_fields["active"] = data["active"]
    
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"message": "User updated"}), 200

@app.route("/api/admin/users/<user_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_user(user_id):
    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404
    
    chats_collection.delete_many({"user_id": user_id})
    return jsonify({"message": "User deleted"}), 200

# ===== AI CHAT ENDPOINTS =====

@app.route("/api/chat", methods=["POST"])
@token_required
def chat():
    if not smart_orchestrator:
        return jsonify({"error": "AI not initialized"}), 503
    
    data = request.json
    question = data.get("question")
    chart_data = data.get("chart_data")
    niche = data.get("niche", "Love & Relationships")
    
    if not question or not chart_data:
        return jsonify({"error": "Question and chart_data required"}), 400
    
    try:
        factors = chart_parser.parse_chart_text(chart_data, niche)
        
        result = smart_orchestrator.answer_question(
            question=question,
            chart_factors=factors,
            niche=niche,
            niche_instruction="",
            conversation_history=[],
            mode="expand"
        )
        
        chat_record = {
            "user_id": request.user["user_id"],
            "question": question,
            "chart_data": chart_data,
            "niche": niche,
            "response": result.response,
            "timestamp": datetime.utcnow()
        }
        chats_collection.insert_one(chat_record)
        
        return jsonify({
            "response": result.response,
            "complexity": result.complexity,
            "passages_used": result.passages_used
        }), 200
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat/history", methods=["GET"])
@token_required
def get_chat_history():
    chats = list(chats_collection.find({"user_id": request.user["user_id"]}).sort("timestamp", -1).limit(50))
    return jsonify([{
        "id": str(c["_id"]),
        "question": c["question"],
        "response": c["response"],
        "niche": c.get("niche", ""),
        "timestamp": c["timestamp"].isoformat()
    } for c in chats]), 200

@app.route("/api/v1/query", methods=["POST"])
@token_required
def query():
    if not smart_orchestrator:
        return jsonify({"error": "AI not initialized"}), 503
    
    data = request.json
    session_id = data.get("session_id", "default")
    question = data.get("question")
    chart_data_obj = data.get("chart_data", {})
    niche = data.get("niche", "love")
    mode = data.get("mode", "expand")
    
    niche_map = {
        "love": "Love & Relationships",
        "career": "Career & Professional",
        "wealth": "Wealth & Finance",
        "health": "Health & Wellness",
        "spiritual": "Spiritual Growth"
    }
    niche_full = niche_map.get(niche, "Love & Relationships")
    
    chart_text = f"""RASHI CHART (D1):
Ascendant: {chart_data_obj.get('ascendant', 'Cancer')}
7th House: {chart_data_obj.get('7th_house_sign', 'Capricorn')}
7th Lord: {chart_data_obj.get('7th_lord', 'Saturn')} in {chart_data_obj.get('7th_lord_placement', '11th house')}
Planets in 7th: {chart_data_obj.get('planets_in_7th', 'Venus')}
Venus: {chart_data_obj.get('venus_sign', 'Capricorn')} in {chart_data_obj.get('venus_house', '7th')} house, {chart_data_obj.get('venus_nakshatra', 'Uttara Ashadha')} pada {chart_data_obj.get('venus_pada', '2')}
Saturn: {chart_data_obj.get('saturn_sign', 'Taurus')} in {chart_data_obj.get('saturn_house', '11th')} house{' (Retrograde)' if chart_data_obj.get('saturn_retrograde') else ''}

NAVAMSA (D9):
Ascendant: {chart_data_obj.get('d9_ascendant', 'Cancer')}
7th House: {chart_data_obj.get('d9_7th_house', 'Capricorn')}
7th Lord: {chart_data_obj.get('d9_7th_lord', 'Saturn')}

Dasha:
Mahadasha: {chart_data_obj.get('current_mahadasha', 'Venus')} ({chart_data_obj.get('current_mahadasha_start', '2020-05-15')} to {chart_data_obj.get('current_mahadasha_end', '2040-05-15')})
Antardasha: {chart_data_obj.get('current_antardasha', 'Saturn')} ({chart_data_obj.get('current_antardasha_start', '2023-11-15')} to {chart_data_obj.get('current_antardasha_end', '2027-01-15')})"""
    
    if not question:
        return jsonify({"error": "Question required"}), 400
    
    try:
        factors = chart_parser.parse_chart_text(chart_text, niche_full)
        
        result = smart_orchestrator.answer_question(
            question=question,
            chart_factors=factors,
            niche=niche_full,
            niche_instruction="",
            conversation_history=[],
            mode=mode
        )
        
        chat_record = {
            "user_id": request.user["user_id"],
            "session_id": session_id,
            "question": question,
            "chart_data": chart_text,
            "niche": niche_full,
            "response": result.response,
            "timestamp": datetime.utcnow()
        }
        chats_collection.insert_one(chat_record)
        
        return jsonify({
            "session_id": session_id,
            "response": result.response,
            "complexity": result.complexity,
            "passages_used": result.passages_used,
            "mode": mode
        }), 200
    
    except Exception as e:
        logger.error(f"Query error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    init_ai()
    app.run(host="0.0.0.0", port=5000, debug=True)
