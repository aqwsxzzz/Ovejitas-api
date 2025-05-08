import { z } from "zod";
import { UserRole } from "../models/user-model";

export const userCreateSchema = z.object({
	displayName: z.string().min(1, "Display name is required"),
	email: z.string().email("Invalid email address"),
	password: z.string().min(8, "Password must be at least 8 characters"),
	isActive: z.boolean().optional(),
	role: z.nativeEnum(UserRole).optional(),
});

export const userUpdateSchema = z.object({
	displayName: z.string().min(1).optional(),
	email: z.string().email().optional(),
	password: z.string().min(8).optional(),
	isActive: z.boolean().optional(),
	role: z.nativeEnum(UserRole).optional(),
});
