import { FindOptions } from 'sequelize';
import { BaseService } from '../../services/base.service';
import { OrderParser, TypedOrderConfig } from '../../utils/order-parser';
import { AnimalMeasurementModel } from './animal-measurement.model';
import { AnimalMeasurementCreate, AnimalMeasurementType, AnimalMeasurementUnit } from './animal-measurement.schema';
import { FilterConfig, FilterConfigBuilder } from '../../utils/filter-parser';

export class AnimalMeasurementService extends BaseService {
	private static readonly ALLOWED_ORDERS = OrderParser.createConfig({
		measuredAt: {
			attribute: 'measuredAt',
		},

	} satisfies TypedOrderConfig);

	private static readonly ALLOWED_FILTERS: FilterConfig = {
		measurementType: FilterConfigBuilder.enum('measurementType', Object.values(AnimalMeasurementType)),
	};

	private static readonly VALID_TYPE_UNIT_MAPPINGS = {
		[AnimalMeasurementType.Weight]: [AnimalMeasurementUnit.Kg],
		[AnimalMeasurementType.Height]: [AnimalMeasurementUnit.Cm],
		[AnimalMeasurementType.Temperature]: [AnimalMeasurementUnit.Celsius],
	};

	async getAnimalMeasurements(animalId: number, order?: string, filters?: Record<string, string>): Promise<AnimalMeasurementModel[]> {
		const ordering = this.parseOrder(order, AnimalMeasurementService.ALLOWED_ORDERS);
		const filterWhere = this.parseFilters(filters, AnimalMeasurementService.ALLOWED_FILTERS);

		const findOptions: FindOptions = { where: { animalId, ...filterWhere } };
		findOptions.order = ordering;

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

			this.validateMeasurementTypeUnit(data.measurementType, data.unit);

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

			const animal = await this.db.models.Animal.findByPk(animalId, { transaction });
			if (!animal) {
				throw new Error('Animal not found');
			}

			await measurement.destroy({ transaction });
		});
	}

	private validateMeasurementTypeUnit(measurementType: AnimalMeasurementType, unit: AnimalMeasurementUnit): void {
		const validUnits = AnimalMeasurementService.VALID_TYPE_UNIT_MAPPINGS[measurementType];
		if (!validUnits || !validUnits.includes(unit)) {
			throw new Error(`Invalid unit '${unit}' for measurement type '${measurementType}'. Valid units are: ${validUnits?.join(', ') || 'none'}`);
		}
	}
}
