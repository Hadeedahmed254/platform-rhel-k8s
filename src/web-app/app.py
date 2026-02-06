from flask import Flask, jsonify, request
import pymysql
import pymongo
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration from environment variables
MARIADB_HOST = os.getenv('MARIADB_HOST', 'mariadb')
MARIADB_USER = os.getenv('MARIADB_USER', 'app_user')
MARIADB_PASSWORD = os.getenv('MARIADB_PASSWORD', 'AppPass123!')
MARIADB_DATABASE = os.getenv('MARIADB_DATABASE', 'enterprise_db')

MONGODB_HOST = os.getenv('MONGODB_HOST', 'mongodb')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
MONGODB_USER = os.getenv('MONGODB_USER', 'app_user')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'AppPass123!')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'enterprise_db')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'web-app'
    }), 200

# Readiness check endpoint
@app.route('/ready', methods=['GET'])
def ready():
    try:
        # Check MariaDB connection
        mariadb_conn = pymysql.connect(
            host=MARIADB_HOST,
            user=MARIADB_USER,
            password=MARIADB_PASSWORD,
            database=MARIADB_DATABASE
        )
        mariadb_conn.close()
        
        # Check MongoDB connection
        mongo_client = pymongo.MongoClient(
            f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}"
        )
        mongo_client.server_info()
        mongo_client.close()
        
        return jsonify({
            'status': 'ready',
            'databases': {
                'mariadb': 'connected',
                'mongodb': 'connected'
            }
        }), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({
            'status': 'not ready',
            'error': str(e)
        }), 503

# Main application endpoint
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Enterprise Platform Web Application',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'ready': '/ready',
            'api': '/api/data'
        }
    }), 200

# Sample API endpoint with database interaction
@app.route('/api/data', methods=['GET', 'POST'])
def api_data():
    if request.method == 'GET':
        try:
            # Fetch data from MongoDB
            mongo_client = pymongo.MongoClient(
                f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}"
            )
            db = mongo_client[MONGODB_DATABASE]
            collection = db['data']
            data = list(collection.find({}, {'_id': 0}).limit(10))
            mongo_client.close()
            
            return jsonify({
                'status': 'success',
                'data': data
            }), 200
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Insert into MongoDB
            mongo_client = pymongo.MongoClient(
                f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}"
            )
            db = mongo_client[MONGODB_DATABASE]
            collection = db['data']
            result = collection.insert_one(data)
            mongo_client.close()
            
            return jsonify({
                'status': 'success',
                'message': 'Data inserted successfully'
            }), 201
        except Exception as e:
            logger.error(f"Error inserting data: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
