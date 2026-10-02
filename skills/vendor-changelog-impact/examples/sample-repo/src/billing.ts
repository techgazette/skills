import Acme from "acme-payments";

const acme = new Acme(process.env.ACME_KEY!);

export async function charge(customerId: string, cardToken: string, amount: number) {
  return acme.charges.create({ customer: customerId, amount, currency: "brl", source: cardToken });
}
