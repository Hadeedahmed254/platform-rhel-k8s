const express = require('express');
const mongoose = require('mongoose');
const morgan = require('morgan');

const app = express();
const PORT = process.env.PORT || 3000;

// MongoDB connection
const MONGODB_URI = process.env.MONGODB_URI || 
  `mongodb://${process.env.MONGODB_USER || 'app_user'}:${process.env.MONGODB_PASSWORD || 'AppPass123!'}@${process.env.MONGODB_HOST || 'mongodb'}:${process.env.MONGODB_PORT || 27017}/${process.env.MONGODB_DATABASE || 'enterprise_db'}`;

// Middleware
app.use(express.json());
app.use(morgan('combined'));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'api-service'
  });
});

// Readiness check endpoint
app.get('/ready', async (req, res) => {
  try {
    if (mongoose.connection.readyState === 1) {
      res.status(200).json({
        status: 'ready',
        database: 'connected'
      });
    } else {
      res.status(503).json({
        status: 'not ready',
        database: 'disconnected'
      });
    }
  } catch (error) {
    res.status(503).json({
      status: 'not ready',
      error: error.message
    });
  }
});

// Main API endpoint
app.get('/api', (req, res) => {
  res.json({
    message: 'Enterprise Platform API Service',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      ready: '/ready',
      items: '/api/items'
    }
  });
});

// Sample CRUD endpoints
const itemSchema = new mongoose.Schema({
  name: String,
  description: String,
  createdAt: { type: Date, default: Date.now }
});

const Item = mongoose.model('Item', itemSchema);

// Get all items
app.get('/api/items', async (req, res) => {
  try {
    const items = await Item.find().limit(100);
    res.json({
      status: 'success',
      count: items.length,
      data: items
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

// Create item
app.post('/api/items', async (req, res) => {
  try {
    const item = new Item(req.body);
    await item.save();
    res.status(201).json({
      status: 'success',
      data: item
    });
  } catch (error) {
    res.status(400).json({
      status: 'error',
      message: error.message
    });
  }
});

// Get item by ID
app.get('/api/items/:id', async (req, res) => {
  try {
    const item = await Item.findById(req.params.id);
    if (!item) {
      return res.status(404).json({
        status: 'error',
        message: 'Item not found'
      });
    }
    res.json({
      status: 'success',
      data: item
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

// Connect to MongoDB and start server
mongoose.connect(MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => {
  console.log('Connected to MongoDB');
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`API Service listening on port ${PORT}`);
  });
})
.catch((error) => {
  console.error('MongoDB connection error:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, closing server...');
  mongoose.connection.close();
  process.exit(0);
});
