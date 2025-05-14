export interface AuthSignUpBody {
	displayName: string;
	email: string;
	password: string;
	language?: string;
	invitationToken?: string;
}
