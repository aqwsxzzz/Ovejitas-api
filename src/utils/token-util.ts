import jwt from "jsonwebtoken";
import crypto from "crypto";

export function createJwtToken(payload: object, secret: string, options?: jwt.SignOptions): string {
	return jwt.sign(payload, secret, options);
}

export function createInvitationToken(): string {
	return crypto.randomBytes(32).toString("hex");
}
