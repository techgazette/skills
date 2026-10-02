import { verify } from "./verify";

export function handle(req: Request, body: string) {
  const sig = req.headers.get("Acme-Signature-V1");
  return verify(body, sig);
}
