const mongoose = require('mongoose');

const connectDb = async ()=>{
    try {
        await mongoose.connect(process.env.DATABASE_URI);
        console.log("mongodb connected successfully");   

    } catch (error) {
        console.error("db not connectd",error);
        process.exit(1);
        
    }
}
module.exports = connectDb