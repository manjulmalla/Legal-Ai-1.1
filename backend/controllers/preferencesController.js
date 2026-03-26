// Preferences Controller
const User = require('../models/userModel');

// Get user preferences
const getPreferences = async (req, res) => {
    try {
        const userId = req.user.id;
        const user = await User.findById(userId).select('-password');
        
        if (!user) {
            return res.status(404).json({ message: 'User not found' });
        }
        
        res.json({
            success: true,
            preferences: user.preferences || {
                topics: [],
                notifications: [],
                language: 'en',
                theme: 'light'
            }
        });
    } catch (error) {
        console.error('Error getting preferences:', error);
        res.status(500).json({ message: 'Server error' });
    }
};

// Save user preferences
const savePreferences = async (req, res) => {
    try {
        const userId = req.user.id;
        const { topics, notifications, language, theme } = req.body;
        
        const user = await User.findById(userId);
        
        if (!user) {
            return res.status(404).json({ message: 'User not found' });
        }
        
        user.preferences = {
            topics: topics || [],
            notifications: notifications || [],
            language: language || 'en',
            theme: theme || 'light'
        };
        
        await user.save();
        
        res.json({
            success: true,
            message: 'Preferences saved successfully',
            preferences: user.preferences
        });
    } catch (error) {
        console.error('Error saving preferences:', error);
        res.status(500).json({ message: 'Server error' });
    }
};

module.exports = { getPreferences, savePreferences };
