import { Database } from '../../database';
import { FarmMemberModel } from './farm-member.model';
import { FarmMemberCreateInput } from './farm-member.schema';

export class FarmMemberService {
	private db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	async createFarmMember(data: FarmMemberCreateInput): Promise<FarmMemberModel> {
		const farmMember = await this.db.models.FarmMember.create(data);
		return farmMember;
	}

	async getFarmMembers(farmId: number): Promise<FarmMemberModel[]> {
		const farmMembers = await this.db.models.FarmMember.findAll({
			where: { farmId },
		});
		return farmMembers;
	}
}
