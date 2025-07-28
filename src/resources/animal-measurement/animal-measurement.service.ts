import { FindOptions } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { OrderParser, TypedOrderConfig } from '../../utils/order-parser';
import { AnimalMeasurementModel } from './animal-measurement.model';
import { AnimalMeasurementCreate } from './animal-measurement.schema';

export class AnimalMeasurementService extends BaseService {
	private static readonly ALLOWED_ORDERS = OrderParser.createConfig({
		measuredAt: {
			attribute: 'measuredAt',
		},

	} satisfies TypedOrderConfig);

	async getAnimalMeasurements(animalId: number, order?: string): Promise<AnimalMeasurementModel[]> {
		const findOptions: FindOptions = { where: { animalId } };
		if (order) {
			// Validate orders before parsing
			this.validateOrder(order, AnimalMeasurementService.ALLOWED_ORDERS);
			findOptions.order = this.parseOrder(order, AnimalMeasurementService.ALLOWED_ORDERS);
		}
		return await this.db.models.AnimalMeasurement.findAll(findOptions);
	}

	async createAnimalMeasurement({ animalId, data, userId }: {
		animalId: number;
		data: AnimalMeasurementCreate;
		userId: number;
	}): Promise<AnimalMeasurementModel> {
		return this.db.sequelize.transaction(async (transaction) => {
			// Validate that the animal exists
			const animal = await this.db.models.Animal.findByPk(animalId, { transaction });
			if (!animal) {
				throw new Error('Animal not found');
			}

			// Create the measurement
			const measurementData = {
				animalId,
				measurementType: data.measurementType,
				value: data.value,
				unit: data.unit,
				measuredAt: data.measuredAt || new Date().toISOString(),
				measuredBy: userId,
				notes: data.notes,
			};

			return this.db.models.AnimalMeasurement.create(measurementData, { transaction });
		});
	}

	async deleteAnimalMeasurement({ animalId, measurementId }: {
		animalId: number;
		measurementId: number;
	}): Promise<void> {
		return this.db.sequelize.transaction(async (transaction) => {
			// Find the measurement to verify it exists and belongs to the animal
			const measurement = await this.db.models.AnimalMeasurement.findOne({
				where: {
					id: measurementId,
					animalId: animalId,
				},
				transaction,
			});

			if (!measurement) {
				throw new Error('Animal measurement not found');
			}

			// Verify the animal exists (additional safety check)
			const animal = await this.db.models.Animal.findByPk(animalId, { transaction });
			if (!animal) {
				throw new Error('Animal not found');
			}

			// Delete the measurement
			await measurement.destroy({ transaction });
		});
	}
}
