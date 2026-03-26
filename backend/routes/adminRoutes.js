const express = require('express');
const router = express.Router();
const { getAdminAnalytics, getAllConversations, deleteConversation } = require('../controllers/adminController');
const verifyToken = require('../middlewares/authMiddleware');

// Protect admin routes
router.get('/', verifyToken, getAdminAnalytics);
router.get('/conversations', verifyToken, getAllConversations);
router.delete('/conversations/:id', verifyToken, deleteConversation);

module.exports = router;
