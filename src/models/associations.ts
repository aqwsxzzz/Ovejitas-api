import { FarmModel } from '../resources/farm/farm.model';
import { UserModel } from '../resources/user/user.model';
import { Species } from './species-model';
import { SpeciesTranslation } from './species-translation-model';
import { Breed } from './breed-model';
import { Animal } from './animal-model';
import { AnimalMeasurement } from './animal-measurement-model';

// Species & SpeciesTranslation
Species.hasMany(SpeciesTranslation, { foreignKey: 'speciesId', as: 'translations' });
SpeciesTranslation.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });

// Species & Breed
Species.hasMany(Breed, { foreignKey: 'speciesId', as: 'breeds' });
Breed.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });

// Animal associations
Animal.belongsTo(FarmModel, { foreignKey: 'farmId', as: 'farm' });
Animal.belongsTo(Species, { foreignKey: 'speciesId', as: 'species' });
Animal.belongsTo(Breed, { foreignKey: 'breedId', as: 'breed' });
Animal.belongsTo(Animal, { foreignKey: 'fatherId', as: 'father' });
Animal.belongsTo(Animal, { foreignKey: 'motherId', as: 'mother' });
Animal.hasMany(Animal, { foreignKey: 'fatherId', as: 'fatheredChildren' });

// AnimalMeasurement associations
AnimalMeasurement.belongsTo(Animal, { foreignKey: 'animalId', as: 'animal' });
AnimalMeasurement.belongsTo(UserModel, { foreignKey: 'measuredBy', as: 'measurer' });
Animal.hasMany(AnimalMeasurement, { foreignKey: 'animalId', as: 'measurements' });
