import app from './app';

const port = process.env.PAPER_PORT || '8082';
app.listen(Number(port), () => {
  console.log(`paper-service listening on ${port}`);
});
