const express = require('express');
const router = express.Router();

// Placeholder routes for portfolio
router.get('/', (req, res) => {
  res.json({ message: 'Portfolio route - coming soon' });
});

router.post('/add', (req, res) => {
  res.json({ message: 'Add to portfolio - coming soon' });
});

router.delete('/remove/:id', (req, res) => {
  res.json({ message: 'Remove from portfolio - coming soon' });
});

module.exports = router;
