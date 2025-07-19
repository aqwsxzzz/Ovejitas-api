import { Database } from '../../database';
import { FarmMemberWithFarm } from '../farm-member/farm-member.schema';
import { FarmModel } from './farm.model';
import { FarmCreateInput, FarmUpdateInput } from './farm.schema';

export class FarmService {
	private db: Database;

	constructor(db: Database) {
		this.db = db;
	}

	async createFarm(data: FarmCreateInput): Promise<FarmModel> {
		const farm = await this.db.models.Farm.create(data);
		return farm;
	}

	async getFarms(userId: number): Promise<FarmModel[]> {
		try {
			const farmMembers = await this.db.models.FarmMember.findAll({
				where: { userId },
				include: [{
					model: FarmModel,
					as: 'farm',
					required: true,
				}],
			}) as FarmMemberWithFarm[];

			return farmMembers.map(member => member.farm);
		} catch (error) {
			console.error('Error fetching farms for user:', userId, error);
			throw new Error('Failed to fetch farms');
		}
	}

	async getFarm(farmId: number): Promise<FarmModel> {
		const farm = await this.db.models.Farm.findByPk(farmId);
		if (!farm) {
			throw new Error('Farm not found');
		}
		return farm;

	}

	async updateFarm(farmId: number, data: FarmUpdateInput): Promise<FarmModel> {
		const farm = await this.db.models.Farm.findByPk(farmId);
		if (!farm) {
			throw new Error('Farm not found');
		}
		await farm.update(data);
		return farm;
	}

	async deleteFarm(farmId: number): Promise<void> {
		const farm = await this.db.models.Farm.findByPk(farmId);
		if (!farm) {
			throw new Error('Farm not found');
		}
		await farm.destroy();
	}

}
