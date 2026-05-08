import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/prisma";

export const DEMO_EMAIL = "demo@outliers.local";
export const DEMO_PASSWORD = "demo-pass";

export const authOptions: NextAuthOptions = {
  // Skipping Prisma adapter on purpose: our User.id is Int, the adapter expects String.
  // Credentials + JWT session strategy doesn't need it.
  session: { strategy: "jwt" },
  pages: { signIn: "/fr/signin" },
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        const email = credentials.email.toLowerCase().trim();

        // Demo seller — auto-provisioned on first sign-in (idempotent)
        if (email === DEMO_EMAIL && credentials.password === DEMO_PASSWORD) {
          let user = await prisma.user.findUnique({ where: { email } });
          if (!user) {
            user = await prisma.user.create({
              data: {
                email,
                name: "Vendeur démo",
                role: "seller",
                passwordHash: await bcrypt.hash(DEMO_PASSWORD, 10),
              },
            });
          }
          return { id: String(user.id), email: user.email, name: user.name, role: user.role };
        }

        // Normal flow
        const user = await prisma.user.findUnique({ where: { email } });
        if (!user || !user.passwordHash) return null;
        const ok = await bcrypt.compare(credentials.password, user.passwordHash);
        if (!ok) return null;
        return { id: String(user.id), email: user.email, name: user.name, role: user.role };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      if (token.id) session.user.id = token.id;
      if (token.role) session.user.role = token.role;
      return session;
    },
  },
};
