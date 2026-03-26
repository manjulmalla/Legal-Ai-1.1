const express = require('express');
const router = express.Router();
const { sendMessage } = require('../controllers/chatController');
const verifyToken = require('../middlewares/authMiddleware');

// Forward POST / to chat sendMessage (requires auth)
router.post('/', verifyToken, sendMessage);

module.exports = router;
