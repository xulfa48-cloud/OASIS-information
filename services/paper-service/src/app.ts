import express from 'express';
import bodyParser from 'body-parser';
import paperRouter from './routes';

const app = express();
app.use(bodyParser.json());

app.use('/api/v1/papers', paperRouter);

app.get('/api/v1/health', (_req, res) => res.json({ status: 'ok' }));
app.get('/api/v1/ready', (_req, res) => res.json({ status: 'ready' }));

export default app;
