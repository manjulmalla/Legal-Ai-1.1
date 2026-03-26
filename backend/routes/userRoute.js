const express = require('express');
const verifyToken = require('../middlewares/authMiddleware')
const router = express.Router();

router.get('/admin', verifyToken ,(req , res)=>{
  return  res.json({message:"this is admin route"})
});

router.get('/manager',(req , res )=>{
  return  res.json({message:"this is admin route"})
});

router.get('/user',(req , res )=>{
   return res.json({message:"this is admin route"})
})
module.exports = router;