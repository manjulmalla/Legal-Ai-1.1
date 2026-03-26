const dns = require('node:dns');
dns.setServers(['8.8.8.8', '1.1.1.1']);

const express = require('express');
require('dotenv').config();

const connectDb = require('./config/db');
const authRoutes = require('./routes/authRoutes');
const userRoutes = require('./routes/userRoute');
const dashboardRoutes = require('./routes/dashboardRoutes');
const chatRoutes = require('./routes/chatRoutes');
const lawRoutes = require('./routes/lawRoutes');
const adminRoutes = require('./routes/adminRoutes');
const askRoutes = require('./routes/askRoutes');
const preferencesRoutes = require('./routes/preferencesRoutes');

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

connectDb();

app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/chat', chatRoutes);
app.use('/api/laws', lawRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/ask', askRoutes);
app.use('/api/preferences', preferencesRoutes);

app.listen(7001, () => {
  console.log("Server is running on port 7001");
});
