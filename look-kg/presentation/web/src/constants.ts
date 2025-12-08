// presentation/web/src/constants.ts
export const CATEGORIES = [
  "blusa","jaqueta","saia","calca","sapato","bolsa","acessorio",
  // ex.: "vestido","cardigan"
] as const;
export type Category = typeof CATEGORIES[number];

export const PATTERNS = ["liso","listrado","xadrez","poa"] as const;
export const STYLES   = ["classico","casual","esportivo","streetwear","formal","romantico"] as const;
export const OCCASIONS= ["casual","formal","esportivo","trabalho","noite"] as const;
export const CLIMES   = ["quente","frio","meia-estacao"] as const;
export const COLORS   = [
  "preto","branco","cinza","nude","bege","marrom",
  "azul","azul-escuro","verde","verde-agua","ciano",
  "vermelho","laranja","amarelo","rosa"
] as const;

// NOVO: material controlado
export const MATERIALS = ["algodao","jeans","couro","seda","linho","la","poliester","malha","metal"] as const;
