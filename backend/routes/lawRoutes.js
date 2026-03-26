const express = require('express');
const router = express.Router();
const { getLaws } = require('../controllers/lawsController');

// Public endpoint that returns law summaries
router.get('/', getLaws);

module.exports = router;
