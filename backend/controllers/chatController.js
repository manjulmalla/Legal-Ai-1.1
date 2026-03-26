const Conversation = require('../models/conversationModel');

// ---------- SAVE MESSAGE ----------
const saveMessage = async (req, res) => {
  try {
    const userId = req.user?.id;
    const { conversationId, message, type } = req.body;

    if (!userId) {
      return res.status(401).json({
        status: 'error',
        message: 'Unauthorized'
      });
    }

    if (!message || !type) {
      return res.status(400).json({
        status: 'error',
        message: 'Message and type are required'
      });
    }

    let conversation;

    if (conversationId) {
      // Update existing conversation
      conversation = await Conversation.findOne({
        _id: conversationId,
        userId: userId
      });

      if (!conversation) {
        return res.status(404).json({
          status: 'error',
          message: 'Conversation not found'
        });
      }
    } else {
      // Create new conversation
      conversation = new Conversation({
        userId: userId,
        title: message.substring(0, 50),
        messages: []
      });
    }

    // Add message to conversation
    conversation.messages.push({
      role: type,
      content: message
    });

    await conversation.save();

    res.status(200).json({
      status: 'success',
      conversationId: conversation._id,
      message: 'Message saved'
    });

  } catch (error) {
    console.error('Save message error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to save message'
    });
  }
};

// ---------- GET CONVERSATION HISTORY ----------
const getConversationHistory = async (req, res) => {
  try {
    const userId = req.user?.id;
    const conversationId = req.params.conversationId;

    if (!userId) {
      return res.status(401).json({
        status: 'error',
        message: 'Unauthorized'
      });
    }

    const conversation = await Conversation.findOne({
      _id: conversationId,
      userId: userId
    });

    if (!conversation) {
      return res.status(404).json({
        status: 'error',
        message: 'Conversation not found'
      });
    }

    res.status(200).json({
      status: 'success',
      data: conversation
    });

  } catch (error) {
    console.error('Get history error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to fetch conversation'
    });
  }
};

// ---------- GET USER CONVERSATIONS ----------
const getUserConversations = async (req, res) => {
  try {
    const userId = req.user?.id;

    if (!userId) {
      return res.status(401).json({
        status: 'error',
        message: 'Unauthorized'
      });
    }

    const conversations = await Conversation.find({ userId: userId })
      .select('_id title createdAt updatedAt')
      .sort({ updatedAt: -1 });

    res.status(200).json({
      status: 'success',
      data: conversations
    });

  } catch (error) {
    console.error('Get conversations error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to fetch conversations'
    });
  }
};

// ---------- SEND MESSAGE AND GET RESPONSE ----------
const sendMessage = async (req, res) => {
  try {
    const userId = req.user?.id;
    const { conversationId, question } = req.body;

    if (!userId) {
      return res.status(401).json({
        status: 'error',
        message: 'Unauthorized'
      });
    }

    if (!question || !question.trim()) {
      return res.status(400).json({
        status: 'error',
        message: 'Question is required'
      });
    }

    let conversation;

    if (conversationId) {
      conversation = await Conversation.findOne({
        _id: conversationId,
        userId: userId
      });
      if (!conversation) {
        return res.status(404).json({
          status: 'error',
          message: 'Conversation not found'
        });
      }
    } else {
      conversation = new Conversation({
        userId: userId,
        title: question.substring(0, 50),
        messages: []
      });
    }

    // Add user message
    conversation.messages.push({
      role: 'user',
      content: question
    });

    // Generate context-aware response based on conversation history
    const botResponse = generateContextAwareResponse(question, conversation.messages);

    // Add bot message
    conversation.messages.push({
      role: 'bot',
      content: botResponse.text,
      citations: botResponse.citations,
      confidence: botResponse.confidence
    });

    await conversation.save();

    res.status(200).json({
      status: 'success',
      conversationId: conversation._id,
      message: botResponse.text,
      citations: botResponse.citations,
      confidence: botResponse.confidence
    });

  } catch (error) {
    console.error('Send message error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to process message'
    });
  }
};

// ---------- GENERATE CONTEXT-AWARE RESPONSE ----------
function generateContextAwareResponse(question, messageHistory) {
  // Extract context from conversation history
  const conversationContext = messageHistory
    .filter(msg => msg.role === 'user')
    .map(msg => msg.content)
    .join(' ');

  // Legal AI Responses Database
  const legalResponses = {
    employment: {
      keywords: ['employment', 'employee', 'employer', 'job', 'work', 'contract', 'wage'],
      responses: [
        'Employees are generally protected against wrongful termination under labor laws.',
        'Employment contracts should clearly define roles, responsibilities, and compensation.',
        'Check the relevant employment laws in your jurisdiction for specific rights.',
        'Workers have the right to a safe working environment under occupational health laws.'
      ],
      citations: ['Muluki Labour Law', 'Constitution of Nepal 2072', 'Employment Act']
    },
    criminal: {
      keywords: ['criminal', 'crime', 'assault', 'theft', 'murder', 'penalty', 'punishment', 'jail'],
      responses: [
        'Criminal liability depends on the jurisdiction and specific laws applicable.',
        'Consult with a criminal defense lawyer immediately for proper legal representation.',
        'Evidence and witness statements are crucial in criminal cases.',
        'The burden of proof in criminal cases is "beyond reasonable doubt".'
      ],
      citations: ['Muluki Criminal Code', 'Criminal Procedure Code', 'Constitution of Nepal 2072']
    },
    property: {
      keywords: ['property', 'land', 'real estate', 'ownership', 'inheritance', 'will', 'deed'],
      responses: [
        'Property rights are protected under property law and the constitution.',
        'Land ownership requires proper documentation and registration.',
        'Inheritance laws vary depending on whether there is a valid will or not.',
        'Property disputes should be resolved through proper legal channels.'
      ],
      citations: ['Land Act', 'Succession Act', 'Real Property Law']
    },
    contract: {
      keywords: ['contract', 'agreement', 'terms', 'liability', 'dispute', 'breach', 'termination'],
      responses: [
        'Contracts must have essential elements: offer, acceptance, consideration, and intention.',
        'Breach of contract can lead to remedies such as damages or specific performance.',
        'Clear contract terms help prevent disputes and misunderstandings.',
        'Contract formation requires mutual consent from both parties.'
      ],
      citations: ['Contract Law', 'Nepalese Civil Code', 'Constitution of Nepal 2072']
    },
    family: {
      keywords: ['marriage', 'divorce', 'custody', 'alimony', 'child', 'family', 'inheritance'],
      responses: [
        'Family laws regulate marriage, divorce, custody, and inheritance matters.',
        'Child custody decisions prioritize the best interest of the child.',
        'Divorce laws vary by jurisdiction and may involve property division.',
        'Marriage registration is important for legal recognition of the relationship.'
      ],
      citations: ['Civil Code', 'Family Law', 'Constitution of Nepal 2072']
    }
  };

  // Determine topic based on keywords
  let topic = 'general';
  let selectedResponses = [];
  let selectedCitations = ['Constitution of Nepal 2072', 'Muluki Law'];

  for (const [key, data] of Object.entries(legalResponses)) {
    const hasKeyword = data.keywords.some(keyword => 
      question.toLowerCase().includes(keyword) || 
      conversationContext.toLowerCase().includes(keyword)
    );
    
    if (hasKeyword) {
      topic = key;
      selectedResponses = data.responses;
      selectedCitations = data.citations;
      break;
    }
  }

  // Select response based on question length and context
  let confidence = 75;
  let responseText;

  if (conversationContext.length > 0) {
    // If there's conversation history, provide more informed response
    confidence = 85;
    responseText = selectedResponses[0];
  } else {
    // New conversation
    confidence = 70;
    responseText = selectedResponses[Math.floor(Math.random() * selectedResponses.length)];
  }

  // Add disclaimer if confidence is low
  if (confidence < 70) {
    responseText += ' ⚠️ It is strongly recommended to consult with a qualified lawyer for accurate legal advice.';
  }

  return {
    text: responseText,
    citations: selectedCitations,
    confidence: confidence,
    topic: topic
  };
}

// ---------- DELETE CONVERSATION ----------
const deleteConversation = async (req, res) => {
  try {
    const userId = req.user?.id;
    const conversationId = req.params.conversationId;

    if (!userId) {
      return res.status(401).json({
        status: 'error',
        message: 'Unauthorized'
      });
    }

    const conversation = await Conversation.findOneAndDelete({
      _id: conversationId,
      userId: userId
    });

    if (!conversation) {
      return res.status(404).json({
        status: 'error',
        message: 'Conversation not found'
      });
    }

    res.status(200).json({
      status: 'success',
      message: 'Conversation deleted'
    });

  } catch (error) {
    console.error('Delete error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to delete conversation'
    });
  }
};

// ---------- CLEANUP OLD CONVERSATIONS ----------
const cleanupOldConversations = async (req, res) => {
  try {
    const { cutoffDate } = req.body;

    if (!cutoffDate) {
      return res.status(400).json({
        status: 'error',
        message: 'Cutoff date is required'
      });
    }

    const result = await Conversation.deleteMany({
      createdAt: { $lt: new Date(cutoffDate) }
    });

    res.status(200).json({
      status: 'success',
      deletedCount: result.deletedCount
    });

  } catch (error) {
    console.error('Cleanup error:', error.message);
    res.status(500).json({
      status: 'error',
      message: 'Failed to cleanup conversations'
    });
  }
};

module.exports = {
  saveMessage,
  getConversationHistory,
  getUserConversations,
  sendMessage,
  deleteConversation,
  cleanupOldConversations
};
