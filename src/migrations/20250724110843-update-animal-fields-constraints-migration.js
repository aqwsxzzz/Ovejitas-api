"use strict";

module.exports = {
	up: async (queryInterface, Sequelize) => {
		// Update breed_id to be NOT NULL and change foreign key to CASCADE
		// First drop the existing foreign key constraint
		await queryInterface.removeConstraint("animals", "animals_breed_id_fkey");
		
		// Make breed_id NOT NULL
		await queryInterface.changeColumn("animals", "breed_id", {
			type: Sequelize.INTEGER.UNSIGNED,
			allowNull: false,
		});
		
		// Add back the foreign key with CASCADE
		await queryInterface.addConstraint("animals", {
			fields: ["breed_id"],
			type: "foreign key",
			name: "animals_breed_id_fkey",
			references: {
				table: "breeds",
				field: "id",
			},
			onDelete: "CASCADE",
		});

		// Make tag_number NOT NULL
		await queryInterface.changeColumn("animals", "tag_number", {
			type: Sequelize.STRING,
			allowNull: false,
		});

		// Make birth_date nullable
		await queryInterface.changeColumn("animals", "birth_date", {
			type: Sequelize.DATE,
			allowNull: true,
		});

		// Make acquisition_date nullable
		await queryInterface.changeColumn("animals", "acquisition_date", {
			type: Sequelize.DATE,
			allowNull: true,
		});

		// Update status enum to remove 'deleted'
		// Create new enum type
		await queryInterface.sequelize.query(`
			CREATE TYPE "enum_animals_status_new" AS ENUM('alive', 'sold', 'deceased');
		`);
		
		// Change column to use new enum
		await queryInterface.sequelize.query(`
			ALTER TABLE animals 
			ALTER COLUMN status TYPE "enum_animals_status_new" 
			USING status::text::"enum_animals_status_new";
		`);
		
		// Drop old enum type
		await queryInterface.sequelize.query(`
			DROP TYPE "enum_animals_status";
		`);
		
		// Rename new enum to original name
		await queryInterface.sequelize.query(`
			ALTER TYPE "enum_animals_status_new" RENAME TO "enum_animals_status";
		`);
	},

	down: async (queryInterface, Sequelize) => {
		// Revert breed_id foreign key to SET NULL
		await queryInterface.removeConstraint("animals", "animals_breed_id_fkey");
		
		// Make breed_id nullable
		await queryInterface.changeColumn("animals", "breed_id", {
			type: Sequelize.INTEGER.UNSIGNED,
			allowNull: true,
		});
		
		// Add back the foreign key with SET NULL
		await queryInterface.addConstraint("animals", {
			fields: ["breed_id"],
			type: "foreign key",
			name: "animals_breed_id_fkey",
			references: {
				table: "breeds",
				field: "id",
			},
			onDelete: "SET NULL",
		});

		// Make tag_number nullable
		await queryInterface.changeColumn("animals", "tag_number", {
			type: Sequelize.STRING,
			allowNull: true,
		});

		// Make birth_date NOT NULL
		await queryInterface.changeColumn("animals", "birth_date", {
			type: Sequelize.DATE,
			allowNull: false,
		});

		// Make acquisition_date NOT NULL
		await queryInterface.changeColumn("animals", "acquisition_date", {
			type: Sequelize.DATE,
			allowNull: false,
		});

		// Restore status enum with 'deleted'
		await queryInterface.sequelize.query(`
			CREATE TYPE "enum_animals_status_new" AS ENUM('alive', 'sold', 'deceased', 'deleted');
		`);
		
		await queryInterface.sequelize.query(`
			ALTER TABLE animals 
			ALTER COLUMN status TYPE "enum_animals_status_new" 
			USING status::text::"enum_animals_status_new";
		`);
		
		await queryInterface.sequelize.query(`
			DROP TYPE "enum_animals_status";
		`);
		
		await queryInterface.sequelize.query(`
			ALTER TYPE "enum_animals_status_new" RENAME TO "enum_animals_status";
		`);
	},
};