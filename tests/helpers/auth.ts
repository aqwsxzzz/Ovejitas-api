import { FastifyInstance } from 'fastify';
import jwt from 'jsonwebtoken';
import { hashPassword } from '../../src/utils/password-util';
import { UserRole } from '../../src/resources/user/user.schema';

const JWT_SECRET = process.env.JWT_SECRET || 'test-jwt-secret';

interface TestUser {
	id: number;
	email: string;
	displayName: string;
	role: string;
	farmId: number;
}

export async function createTestUser(app: FastifyInstance): Promise<TestUser> {
	const hashedPassword = await hashPassword('testpassword123');
	const user = await app.db.models.User.create({
		displayName: 'Test User',
		email: `test-${Date.now()}@example.com`,
		password: hashedPassword,
	});

	const farm = await app.db.models.Farm.create({
		name: 'Test Farm',
	});

	await app.db.models.FarmMember.create({
		farmId: farm.dataValues.id,
		userId: user.dataValues.id,
		role: 'owner',
	});

	user.setDataValue('lastVisitedFarmId', farm.dataValues.id);
	await user.save();

	return {
		id: user.dataValues.id,
		email: user.dataValues.email,
		displayName: user.dataValues.displayName,
		role: user.dataValues.role,
		farmId: farm.dataValues.id,
	};
}

export function getAuthCookie(user: TestUser): string {
	const token = jwt.sign(
		{ id: user.id, email: user.email, role: UserRole.USER },
		JWT_SECRET,
		{ expiresIn: '1d' },
	);
	return `jwt=${token}`;
}

export async function createAuthenticatedUser(app: FastifyInstance): Promise<{ user: TestUser; cookie: string }> {
	const user = await createTestUser(app);
	const cookie = getAuthCookie(user);
	return { user, cookie };
}
