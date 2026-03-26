const express = require('express');
const router = express.Router();
const {
  saveMessage,
  getConversationHistory,
  getUserConversations,
  sendMessage,
  deleteConversation,
  cleanupOldConversations
} = require('../controllers/chatController');
const verifyToken = require('../middlewares/authMiddleware');

// All chat routes require authentication
router.use(verifyToken);

// Send message and get response
router.post('/message', sendMessage);

// Save message (without getting response)
router.post('/save', saveMessage);

// Get user's conversations
router.get('/conversations', getUserConversations);

// Get specific conversation history
router.get('/conversations/:conversationId', getConversationHistory);

// Delete conversation
router.delete('/conversations/:conversationId', deleteConversation);

// Cleanup old conversations (admin/internal use)
router.post('/cleanup', cleanupOldConversations);

module.exports = router;
