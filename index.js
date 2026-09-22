require('dotenv').config();
const mongoose = require('mongoose');
const axios = require('axios');
const cron = require('node-cron');

mongoose.connect(process.env.MONGO_URI).then(() => {
  console.log('✅ Connected to eurusd database!');
}).catch(e => console.log('❌ Mongo Error:', e.message));

const priceSchema = new mongoose.Schema({
  pair: String,
  price: Number,
  time: { type: Date, default: Date.now }
});
const Price = mongoose.model('Price', priceSchema);

async function saveEURUSD() {
  try {
    const res = await axios.get('https://api.exchangerate-api.com/v4/latest/EUR');
    const price = res.data.rates.USD;
    await new Price({ pair: 'EURUSD', price: price }).save();
    console.log(`💾 Saved EURUSD: ${price} at ${new Date().toLocaleTimeString()}`);
  } catch (err) {
    console.log('Error fetching:', err.message);
  }
}

cron.schedule('* * * * *', saveEURUSD);
saveEURUSD();
