import { PrismaClient } from "@/generated/prisma";

// Singleton — avoid re-instantiating the client on every hot-reload in dev.
const g = globalThis as unknown as { prisma?: PrismaClient };

export const prisma = g.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== "production") g.prisma = prisma;
