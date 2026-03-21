#!/usr/bin/env node
'use strict';

/**
 * Dev seed script — creates a full demo dataset for local development.
 * Run: docker compose exec app node src/scripts/dev-seed.js
 *
 * Creates:
 *   - 1 user (testuser@test.com / Password1)
 *   - 1 farm + owner membership
 *   - 15 animals across all species/breeds
 *   - 40+ measurements (weight, height, temperature) per animal
 *   - 30+ financial transactions (expenses & income)
 */

// eslint-disable-next-line @typescript-eslint/no-require-imports
require('dotenv').config();
const { Sequelize } = require('sequelize');
const bcrypt = require('bcryptjs');

const sequelize = new Sequelize({
	dialect: 'postgres',
	host: process.env.DB_HOST,
	port: Number(process.env.DB_PORT),
	username: process.env.DB_USER,
	password: process.env.DB_PASS,
	database: process.env.DB_NAME,
	logging: false,
});

async function query(sql, replacements) {
	const [rows] = await sequelize.query(sql, { replacements });
	return rows;
}

async function queryOne(sql, replacements) {
	const rows = await query(sql, replacements);
	return rows[0];
}

async function main() {
	await sequelize.authenticate();
	console.log('Connected to database.');

	const now = new Date();

	// --- User (skip if exists) ---
	let existingUser = await queryOne(
		"SELECT id FROM users WHERE email = 'testuser@test.com'",
	);
	let userId;
	let farmId;

	if (existingUser) {
		userId = existingUser.id;
		const existingFarm = await queryOne(
			'SELECT farm_id FROM farm_members WHERE user_id = :userId AND role = \'owner\' LIMIT 1',
			{ userId },
		);
		farmId = existingFarm.farm_id;
		console.log(`User already exists (id: ${userId}, farmId: ${farmId}). Skipping user/farm setup.`);
	} else {
		const hashedPassword = await bcrypt.hash('Password1', 10);
		const user = await queryOne(
			`INSERT INTO users (display_name, email, password, is_active, role, language, created_at, updated_at)
			 VALUES ('Test User', 'testuser@test.com', :password, true, 'user', 'en', :now, :now)
			 RETURNING id`,
			{ password: hashedPassword, now },
		);
		userId = user.id;
		console.log(`Created user (id: ${userId})`);

		const farm = await queryOne(
			`INSERT INTO farms (name, created_at, updated_at)
			 VALUES ('Demo Farm', :now, :now)
			 RETURNING id`,
			{ now },
		);
		farmId = farm.id;
		console.log(`Created farm (id: ${farmId})`);

		await query(
			`INSERT INTO farm_members (farm_id, user_id, role, created_at, updated_at)
			 VALUES (:farmId, :userId, 'owner', :now, :now)`,
			{ farmId, userId, now },
		);

		await query(
			`UPDATE users SET last_visited_farm_id = :farmId WHERE id = :userId`,
			{ farmId, userId },
		);
	}

	// --- Look up species & breed IDs ---
	const speciesRows = await query(
		`SELECT s.id, st.name
		 FROM species s
		 JOIN species_translation st ON st.species_id = s.id
		 WHERE st.language_code = 'en'`,
	);
	const species = {};
	for (const row of speciesRows) {
		species[row.name] = row.id;
	}

	const breedRows = await query(
		`SELECT b.id, b.species_id, bt.name
		 FROM breeds b
		 JOIN breed_translation bt ON bt.breed_id = b.id
		 WHERE bt.language_code = 'en'`,
	);
	const breeds = {};
	for (const row of breedRows) {
		const speciesName = speciesRows.find((s) => s.id === row.species_id)?.name;
		if (speciesName) {
			breeds[`${speciesName}:${row.name}`] = row.id;
		}
	}

	// --- Animals (skip if exists) ---
	const existingAnimals = await queryOne(
		'SELECT COUNT(*) as count FROM animals WHERE farm_id = :farmId',
		{ farmId },
	);

	let animalIds = [];
	if (Number(existingAnimals.count) > 0) {
		const rows = await query(
			`SELECT a.id, a.tag_number as tag FROM animals a WHERE a.farm_id = :farmId`,
			{ farmId },
		);
		animalIds = rows.map((r) => ({ id: r.id, tag: r.tag }));
		console.log(`Animals already exist (${animalIds.length}). Skipping.`);
	} else {
	const animalDefs = [
		// Sheep (5)
		{ name: 'Luna', tag: 'SH-001', species: 'Sheep', breed: 'Suffolk', sex: 'female', status: 'alive', repro: 'pregnant', acq: 'purchased', birthDate: '2024-03-15' },
		{ name: 'Rex', tag: 'SH-002', species: 'Sheep', breed: 'Merino', sex: 'male', status: 'alive', repro: 'other', acq: 'born', birthDate: '2024-06-01' },
		{ name: 'Dolly', tag: 'SH-003', species: 'Sheep', breed: 'Suffolk', sex: 'female', status: 'alive', repro: 'lactating', acq: 'born', birthDate: '2024-01-10' },
		{ name: 'Wooly', tag: 'SH-004', species: 'Sheep', breed: 'Merino', sex: 'female', status: 'alive', repro: 'open', acq: 'purchased', birthDate: '2023-09-22' },
		{ name: 'Patch', tag: 'SH-005', species: 'Sheep', breed: 'Other', sex: 'male', status: 'sold', repro: 'other', acq: 'born', birthDate: '2024-04-18' },
		// Cattle (4)
		{ name: 'Bessie', tag: 'CA-001', species: 'Cattle', breed: 'Holstein', sex: 'female', status: 'alive', repro: 'lactating', acq: 'purchased', birthDate: '2023-01-20' },
		{ name: 'Bruno', tag: 'CA-002', species: 'Cattle', breed: 'Angus', sex: 'male', status: 'alive', repro: 'other', acq: 'purchased', birthDate: '2023-08-10' },
		{ name: 'Daisy', tag: 'CA-003', species: 'Cattle', breed: 'Holstein', sex: 'female', status: 'alive', repro: 'pregnant', acq: 'purchased', birthDate: '2022-11-05' },
		{ name: 'Thor', tag: 'CA-004', species: 'Cattle', breed: 'Angus', sex: 'male', status: 'alive', repro: 'other', acq: 'born', birthDate: '2024-02-14' },
		// Goats (3)
		{ name: 'Pepper', tag: 'GO-001', species: 'Goat', breed: 'Boer', sex: 'female', status: 'alive', repro: 'open', acq: 'born', birthDate: '2025-01-05' },
		{ name: 'Clover', tag: 'GO-002', species: 'Goat', breed: 'Saanen', sex: 'female', status: 'alive', repro: 'pregnant', acq: 'purchased', birthDate: '2024-07-12' },
		{ name: 'Billy', tag: 'GO-003', species: 'Goat', breed: 'Boer', sex: 'male', status: 'alive', repro: 'other', acq: 'purchased', birthDate: '2024-03-30' },
		// Pigs (3)
		{ name: 'Hamlet', tag: 'PI-001', species: 'Pig', breed: 'Yorkshire', sex: 'male', status: 'alive', repro: 'other', acq: 'purchased', birthDate: '2024-11-20' },
		{ name: 'Truffle', tag: 'PI-002', species: 'Pig', breed: 'Duroc', sex: 'female', status: 'alive', repro: 'pregnant', acq: 'purchased', birthDate: '2024-08-03' },
		{ name: 'Bacon', tag: 'PI-003', species: 'Pig', breed: 'Yorkshire', sex: 'male', status: 'deceased', repro: 'other', acq: 'born', birthDate: '2024-05-15' },
	];

	for (const a of animalDefs) {
		const speciesId = species[a.species];
		const breedId = breeds[`${a.species}:${a.breed}`];
		const animal = await queryOne(
			`INSERT INTO animals (farm_id, species_id, breed_id, name, tag_number, sex, birth_date, status, reproductive_status, acquisition_type, created_at, updated_at)
			 VALUES (:farmId, :speciesId, :breedId, :name, :tag, :sex, :birthDate, :status, :repro, :acq, :now, :now)
			 RETURNING id`,
			{ farmId, speciesId, breedId, name: a.name, tag: a.tag, sex: a.sex, birthDate: a.birthDate, status: a.status, repro: a.repro, acq: a.acq, now },
		);
		animalIds.push({ id: animal.id, ...a });
	}
	console.log(`Created ${animalIds.length} animals`);
	}

	// --- Measurements (skip if exists) ---
	const existingMeasurements = await queryOne(
		'SELECT COUNT(*) as count FROM animal_measurements',
	);

	if (Number(existingMeasurements.count) > 0) {
		console.log('Measurements already exist. Skipping.');
	} else {
	let measurementCount = 0;
	const measurementDefs = [
		// Sheep weights (history over time)
		{ tag: 'SH-001', type: 'weight', value: 58.0, unit: 'kg', daysAgo: 90 },
		{ tag: 'SH-001', type: 'weight', value: 62.3, unit: 'kg', daysAgo: 60 },
		{ tag: 'SH-001', type: 'weight', value: 65.5, unit: 'kg', daysAgo: 30 },
		{ tag: 'SH-001', type: 'weight', value: 68.2, unit: 'kg', daysAgo: 7 },
		{ tag: 'SH-002', type: 'weight', value: 40.0, unit: 'kg', daysAgo: 45 },
		{ tag: 'SH-002', type: 'weight', value: 45.0, unit: 'kg', daysAgo: 14 },
		{ tag: 'SH-003', type: 'weight', value: 70.0, unit: 'kg', daysAgo: 60 },
		{ tag: 'SH-003', type: 'weight', value: 72.5, unit: 'kg', daysAgo: 20 },
		{ tag: 'SH-004', type: 'weight', value: 55.0, unit: 'kg', daysAgo: 30 },
		{ tag: 'SH-004', type: 'weight', value: 57.8, unit: 'kg', daysAgo: 5 },
		{ tag: 'SH-005', type: 'weight', value: 48.0, unit: 'kg', daysAgo: 40 },
		// Cattle weights
		{ tag: 'CA-001', type: 'weight', value: 500.0, unit: 'kg', daysAgo: 60 },
		{ tag: 'CA-001', type: 'weight', value: 520.0, unit: 'kg', daysAgo: 21 },
		{ tag: 'CA-001', type: 'weight', value: 535.0, unit: 'kg', daysAgo: 3 },
		{ tag: 'CA-002', type: 'weight', value: 460.0, unit: 'kg', daysAgo: 45 },
		{ tag: 'CA-002', type: 'weight', value: 480.0, unit: 'kg', daysAgo: 10 },
		{ tag: 'CA-003', type: 'weight', value: 490.0, unit: 'kg', daysAgo: 30 },
		{ tag: 'CA-003', type: 'weight', value: 510.0, unit: 'kg', daysAgo: 5 },
		{ tag: 'CA-004', type: 'weight', value: 350.0, unit: 'kg', daysAgo: 60 },
		{ tag: 'CA-004', type: 'weight', value: 390.0, unit: 'kg', daysAgo: 14 },
		// Goat weights
		{ tag: 'GO-001', type: 'weight', value: 35.0, unit: 'kg', daysAgo: 30 },
		{ tag: 'GO-001', type: 'weight', value: 38.5, unit: 'kg', daysAgo: 5 },
		{ tag: 'GO-002', type: 'weight', value: 42.0, unit: 'kg', daysAgo: 25 },
		{ tag: 'GO-002', type: 'weight', value: 45.0, unit: 'kg', daysAgo: 3 },
		{ tag: 'GO-003', type: 'weight', value: 55.0, unit: 'kg', daysAgo: 20 },
		{ tag: 'GO-003', type: 'weight', value: 58.5, unit: 'kg', daysAgo: 2 },
		// Pig weights
		{ tag: 'PI-001', type: 'weight', value: 95.0, unit: 'kg', daysAgo: 40 },
		{ tag: 'PI-001', type: 'weight', value: 110.0, unit: 'kg', daysAgo: 7 },
		{ tag: 'PI-002', type: 'weight', value: 85.0, unit: 'kg', daysAgo: 35 },
		{ tag: 'PI-002', type: 'weight', value: 98.0, unit: 'kg', daysAgo: 8 },
		{ tag: 'PI-003', type: 'weight', value: 70.0, unit: 'kg', daysAgo: 50 },
		// Heights
		{ tag: 'SH-001', type: 'height', value: 72.0, unit: 'cm', daysAgo: 30 },
		{ tag: 'SH-002', type: 'height', value: 65.0, unit: 'cm', daysAgo: 14 },
		{ tag: 'SH-003', type: 'height', value: 74.0, unit: 'cm', daysAgo: 20 },
		{ tag: 'CA-001', type: 'height', value: 145.0, unit: 'cm', daysAgo: 21 },
		{ tag: 'CA-002', type: 'height', value: 138.0, unit: 'cm', daysAgo: 10 },
		{ tag: 'CA-003', type: 'height', value: 142.0, unit: 'cm', daysAgo: 30 },
		{ tag: 'CA-004', type: 'height', value: 125.0, unit: 'cm', daysAgo: 14 },
		{ tag: 'GO-001', type: 'height', value: 65.0, unit: 'cm', daysAgo: 5 },
		{ tag: 'GO-002', type: 'height', value: 68.0, unit: 'cm', daysAgo: 3 },
		{ tag: 'GO-003', type: 'height', value: 72.0, unit: 'cm', daysAgo: 2 },
		{ tag: 'PI-001', type: 'height', value: 75.0, unit: 'cm', daysAgo: 7 },
		{ tag: 'PI-002', type: 'height', value: 70.0, unit: 'cm', daysAgo: 8 },
		// Temperatures
		{ tag: 'SH-001', type: 'temperature', value: 39.2, unit: 'celsius', daysAgo: 7 },
		{ tag: 'SH-003', type: 'temperature', value: 39.5, unit: 'celsius', daysAgo: 10 },
		{ tag: 'CA-001', type: 'temperature', value: 38.8, unit: 'celsius', daysAgo: 3 },
		{ tag: 'CA-003', type: 'temperature', value: 39.0, unit: 'celsius', daysAgo: 5 },
		{ tag: 'GO-002', type: 'temperature', value: 39.3, unit: 'celsius', daysAgo: 3 },
		{ tag: 'PI-001', type: 'temperature', value: 38.5, unit: 'celsius', daysAgo: 7 },
		{ tag: 'PI-002', type: 'temperature', value: 39.8, unit: 'celsius', daysAgo: 2 },
	];

	for (const m of measurementDefs) {
		const animal = animalIds.find((a) => a.tag === m.tag);
		if (!animal) continue;
		const measuredAt = new Date(now.getTime() - m.daysAgo * 24 * 60 * 60 * 1000);
		const measurement = await queryOne(
			`INSERT INTO animal_measurements (animal_id, measurement_type, value, unit, measured_at, measured_by, created_at, updated_at)
			 VALUES (:animalId, :type, :value, :unit, :measuredAt, :userId, :now, :now)
			 RETURNING id`,
			{ animalId: animal.id, type: m.type, value: m.value, unit: m.unit, measuredAt, userId, now },
		);

		// Link latest weight measurement to animal
		if (m.type === 'weight') {
			await query(
				`UPDATE animals SET weight_id = :measurementId WHERE id = :animalId`,
				{ measurementId: measurement.id, animalId: animal.id },
			);
		}
		measurementCount++;
	}
	console.log(`Created ${measurementCount} measurements`);
	}

	// --- Financial Transactions (skip if exists) ---
	const existingTransactions = await queryOne(
		'SELECT COUNT(*) as count FROM financial_transactions WHERE farm_id = :farmId',
		{ farmId },
	);

	if (Number(existingTransactions.count) > 0) {
		console.log('Financial transactions already exist. Skipping.');
	} else {
	const transactionDefs = [
		// Expenses — Sheep
		{ type: 'expense', date: '2025-11-15', amount: 800.00, desc: 'Sheep shearing service', speciesKey: 'Sheep' },
		{ type: 'expense', date: '2025-12-01', amount: 1500.00, desc: 'Monthly feed supply - hay and grain', speciesKey: 'Sheep' },
		{ type: 'expense', date: '2025-12-05', amount: 350.00, desc: 'Vaccination - all sheep', speciesKey: 'Sheep' },
		{ type: 'expense', date: '2026-01-10', amount: 1200.00, desc: 'Sheep feed - January', speciesKey: 'Sheep' },
		{ type: 'expense', date: '2026-02-05', amount: 280.00, desc: 'Deworming - sheep flock', speciesKey: 'Sheep' },
		{ type: 'expense', date: '2026-03-01', amount: 1400.00, desc: 'March feed - sheep', speciesKey: 'Sheep' },
		// Expenses — Cattle
		{ type: 'expense', date: '2025-12-10', amount: 2800.00, desc: 'Cattle feed - silage delivery', speciesKey: 'Cattle' },
		{ type: 'expense', date: '2026-01-25', amount: 275.00, desc: 'Hoof trimming - cattle', speciesKey: 'Cattle' },
		{ type: 'expense', date: '2026-02-01', amount: 3200.00, desc: 'New water troughs', speciesKey: 'Cattle' },
		{ type: 'expense', date: '2026-02-15', amount: 600.00, desc: 'Veterinary checkup - cattle', speciesKey: 'Cattle' },
		{ type: 'expense', date: '2026-03-10', amount: 2500.00, desc: 'Silage delivery - March', speciesKey: 'Cattle' },
		// Expenses — Goat
		{ type: 'expense', date: '2025-12-15', amount: 450.00, desc: 'Deworming treatment - goats', speciesKey: 'Goat' },
		{ type: 'expense', date: '2026-02-10', amount: 950.00, desc: 'Goat mineral supplements - bulk', speciesKey: 'Goat' },
		{ type: 'expense', date: '2026-03-05', amount: 320.00, desc: 'Goat feed - March', speciesKey: 'Goat' },
		// Expenses — Pig
		{ type: 'expense', date: '2026-01-15', amount: 500.00, desc: 'Pig feed - special mix', speciesKey: 'Pig' },
		{ type: 'expense', date: '2026-02-20', amount: 380.00, desc: 'Pig supplements', speciesKey: 'Pig' },
		{ type: 'expense', date: '2026-03-12', amount: 550.00, desc: 'Pig feed - March', speciesKey: 'Pig' },
		// Income — Sheep
		{ type: 'income', date: '2025-12-20', amount: 2400.00, desc: 'Wool sale - December batch', speciesKey: 'Sheep' },
		{ type: 'income', date: '2026-01-18', amount: 1800.00, desc: 'Sold 2 lambs at market', speciesKey: 'Sheep' },
		{ type: 'income', date: '2026-03-08', amount: 3200.00, desc: 'Wool sale - March shearing', speciesKey: 'Sheep' },
		// Income — Cattle
		{ type: 'income', date: '2026-01-05', amount: 5500.00, desc: 'Sold 1 steer at auction', speciesKey: 'Cattle' },
		{ type: 'income', date: '2026-02-12', amount: 1200.00, desc: 'Milk sales - February', speciesKey: 'Cattle' },
		{ type: 'income', date: '2026-03-15', amount: 1350.00, desc: 'Milk sales - March', speciesKey: 'Cattle' },
		// Income — Goat
		{ type: 'income', date: '2026-01-22', amount: 900.00, desc: 'Goat cheese sales - January', speciesKey: 'Goat' },
		{ type: 'income', date: '2026-02-25', amount: 1100.00, desc: 'Goat cheese sales - February', speciesKey: 'Goat' },
		{ type: 'income', date: '2026-03-18', amount: 950.00, desc: 'Goat milk sales - March', speciesKey: 'Goat' },
		// Income — Pig
		{ type: 'income', date: '2026-02-08', amount: 4200.00, desc: 'Sold 3 pigs at market', speciesKey: 'Pig' },
		{ type: 'income', date: '2026-03-20', amount: 1500.00, desc: 'Pork pre-orders', speciesKey: 'Pig' },
	];

	let transactionCount = 0;
	for (const t of transactionDefs) {
		const speciesId = species[t.speciesKey];
		await query(
			`INSERT INTO financial_transactions (farm_id, type, amount, description, species_id, date, created_by, created_at, updated_at)
			 VALUES (:farmId, :type, :amount, :desc, :speciesId, :date, :userId, :now, :now)`,
			{
				farmId, type: t.type, amount: t.amount, desc: t.desc,
				speciesId, date: t.date, userId, now,
			},
		);
		transactionCount++;
	}
	console.log(`Created ${transactionCount} financial transactions`);
	}

	console.log('\nDev seed complete!');
	console.log('Login: testuser@test.com / Password1');
}

main()
	.catch((err) => {
		console.error('Dev seed failed:', err);
		process.exit(1);
	})
	.finally(() => sequelize.close());
