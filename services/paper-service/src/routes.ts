import { Router, Request, Response } from 'express';
import { createPaper, getPaper, searchPapers } from './controllers/paperController';

const router = Router();

router.post('/', async (req: Request, res: Response) => {
  const result = await createPaper(req.body);
  res.status(201).json(result);
});

router.get('/:id', async (req: Request, res: Response) => {
  const id = req.params.id;
  const p = await getPaper(id);
  if (!p) return res.status(404).json({ error: 'not found' });
  return res.json(p);
});

router.post('/search', async (req: Request, res: Response) => {
  const results = await searchPapers(req.body);
  res.json({ results });
});

export default router;
