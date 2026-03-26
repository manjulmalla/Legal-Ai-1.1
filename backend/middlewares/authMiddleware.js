const jwt = require('jsonwebtoken');

const verifyToken = (req, res, next) => {
    try {
        const authHeader = req.headers.authorization || req.headers.Authorization;
        if (!authHeader || typeof authHeader !== 'string') {
            return res.status(401).json({ message: 'No token provided' });
        }

        if (!authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ message: 'Invalid token format' });
        }

        const token = authHeader.split(' ')[1];
        if (!token) {
            return res.status(401).json({ message: 'No token provided' });
        }

        const decoded = jwt.verify(token, process.env.JWT_SECRET_KEY);
        req.user = decoded;
        next();
    } catch (error) {
        return res.status(401).json({ message: 'Token verification failed' });
    }
};

module.exports = verifyToken;