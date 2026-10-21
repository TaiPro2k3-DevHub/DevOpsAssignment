import express from 'express';
import serverlessExpress from '@codegenie/serverless-express';

const app = express();
app.use(express.json());

app.get('/', (req, res) => {
  res.json({
    message: 'Hello từ ExpressJS + PNPM trên AWS Lambda! ⚡️',
    timestamp: Date.now()
  });
});

app.get('/test', (req, res) => {
  res.json({ status: 'ok', pnpm: true });
});

// Handler bọc Express
export const handler = serverlessExpress({ app });
