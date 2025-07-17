'use strict';

/** @type {import('sequelize-cli').Migration} */
module.exports = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('animal_measurements', {
      id: {
        type: Sequelize.BIGINT,
        primaryKey: true,
        autoIncrement: true,
        allowNull: false
      },
      animal_id: {
        type: Sequelize.BIGINT,
        allowNull: false,
        references: {
          model: 'animals',
          key: 'id'
        },
        onUpdate: 'CASCADE',
        onDelete: 'CASCADE'
      },
      measurement_type: {
        type: Sequelize.ENUM('weight', 'height', 'body_condition'),
        allowNull: false
      },
      value: {
        type: Sequelize.DECIMAL(10, 2),
        allowNull: false,
        validate: {
          min: 0
        }
      },
      unit: {
        type: Sequelize.STRING(10),
        allowNull: false
      },
      measured_at: {
        type: Sequelize.DATE,
        allowNull: false,
        defaultValue: Sequelize.NOW
      },
      measured_by: {
        type: Sequelize.BIGINT,
        allowNull: true,
        references: {
          model: 'users',
          key: 'id'
        },
        onUpdate: 'CASCADE',
        onDelete: 'SET NULL'
      },
      method: {
        type: Sequelize.STRING(50),
        allowNull: true
      },
      notes: {
        type: Sequelize.TEXT,
        allowNull: true
      },
      created_at: {
        type: Sequelize.DATE,
        allowNull: false,
        defaultValue: Sequelize.NOW
      },
      updated_at: {
        type: Sequelize.DATE,
        allowNull: false,
        defaultValue: Sequelize.NOW
      }
    });

    // Create indexes for performance
    await queryInterface.addIndex('animal_measurements', {
      fields: ['animal_id', 'measurement_type', 'measured_at'],
      name: 'idx_animal_measurements_animal_type_time'
    });

    await queryInterface.addIndex('animal_measurements', {
      fields: ['measured_at'],
      name: 'idx_animal_measurements_time'
    });

    await queryInterface.addIndex('animal_measurements', {
      fields: ['animal_id'],
      name: 'idx_animal_measurements_animal_id'
    });
  },

  async down(queryInterface, Sequelize) {
    await queryInterface.dropTable('animal_measurements');
  }
};