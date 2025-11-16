"""
Flask API for User Authentication and AI Chat
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import hash_password, verify_password, create_token, token_required, admin_required
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

@app.route("/api/signup", methods=["POST"])
def signup():
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

@app.route("/api/login", methods=["POST"])
def login():
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
            mode="draft"
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

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    init_ai()
    app.run(host="0.0.0.0", port=5000, debug=True)
