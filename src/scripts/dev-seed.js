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
 *   - 15+ expenses across categories
 *   - 2 chicken flocks with flock events and egg collections
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

	// --- Check if already seeded ---
	const existing = await queryOne(
		"SELECT id FROM users WHERE email = 'testuser@test.com'",
	);
	if (existing) {
		console.log('Dev seed data already exists. Skipping.');
		return;
	}

	// --- User ---
	const hashedPassword = await bcrypt.hash('Password1', 10);
	const user = await queryOne(
		`INSERT INTO users (display_name, email, password, is_active, role, language, created_at, updated_at)
		 VALUES ('Test User', 'testuser@test.com', :password, true, 'user', 'en', :now, :now)
		 RETURNING id`,
		{ password: hashedPassword, now },
	);
	const userId = user.id;
	console.log(`Created user (id: ${userId})`);

	// --- Farm ---
	const farm = await queryOne(
		`INSERT INTO farms (name, created_at, updated_at)
		 VALUES ('Demo Farm', :now, :now)
		 RETURNING id`,
		{ now },
	);
	const farmId = farm.id;
	console.log(`Created farm (id: ${farmId})`);

	// --- Farm membership (owner) ---
	await query(
		`INSERT INTO farm_members (farm_id, user_id, role, created_at, updated_at)
		 VALUES (:farmId, :userId, 'owner', :now, :now)`,
		{ farmId, userId, now },
	);

	// --- Update user last_visited_farm_id ---
	await query(
		`UPDATE users SET last_visited_farm_id = :farmId WHERE id = :userId`,
		{ farmId, userId },
	);

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

	// --- Animals ---
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

	const animalIds = [];
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

	// --- Measurements ---
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

	// --- Expenses ---
	const expenseDefs = [
		{ date: '2025-11-15', amount: 800.00, desc: 'Sheep shearing service', category: 'labor', speciesKey: 'Sheep', vendor: 'Shear Pros', payment: 'cash', qty: 5, qtyUnit: 'hours', unitCost: 160.00, status: 'paid' },
		{ date: '2025-12-01', amount: 1500.00, desc: 'Monthly feed supply - hay and grain', category: 'feed', speciesKey: 'Sheep', vendor: 'FarmFeed Co.', payment: 'bank_transfer', qty: 500, qtyUnit: 'kg', unitCost: 3.00, status: 'paid' },
		{ date: '2025-12-05', amount: 350.00, desc: 'Vaccination - all sheep', category: 'veterinary', speciesKey: 'Sheep', vendor: 'Dr. Martinez', payment: 'cash', qty: 5, qtyUnit: 'doses', unitCost: 70.00, status: 'paid' },
		{ date: '2025-12-10', amount: 2800.00, desc: 'Cattle feed - silage delivery', category: 'feed', speciesKey: 'Cattle', vendor: 'AgriSupply', payment: 'credit_card', qty: 1000, qtyUnit: 'kg', unitCost: 2.80, status: 'paid' },
		{ date: '2025-12-15', amount: 450.00, desc: 'Deworming treatment - goats', category: 'veterinary', speciesKey: 'Goat', vendor: 'Dr. Martinez', payment: 'cash', qty: 3, qtyUnit: 'doses', unitCost: 150.00, status: 'paid' },
		{ date: '2025-12-18', amount: 120.00, desc: 'Electricity bill - December', category: 'utilities', vendor: 'Power Co.', payment: 'bank_transfer', status: 'paid' },
		{ date: '2025-12-20', amount: 200.00, desc: 'Fence repair materials', category: 'maintenance', vendor: 'Hardware Store', payment: 'debit_card', qty: 10, qtyUnit: 'units', unitCost: 20.00, status: 'paid' },
		{ date: '2026-01-02', amount: 1800.00, desc: 'January feed order - mixed', category: 'feed', vendor: 'FarmFeed Co.', payment: 'bank_transfer', qty: 600, qtyUnit: 'kg', unitCost: 3.00, status: 'paid' },
		{ date: '2026-01-10', amount: 150.00, desc: 'Transport to market', category: 'transport', vendor: 'Rural Transport', payment: 'cash', status: 'paid' },
		{ date: '2026-01-15', amount: 500.00, desc: 'Pig feed - special mix', category: 'feed', speciesKey: 'Pig', vendor: 'FarmFeed Co.', payment: 'bank_transfer', qty: 200, qtyUnit: 'kg', unitCost: 2.50, status: 'paid' },
		{ date: '2026-01-20', amount: 125.00, desc: 'Electricity bill - January', category: 'utilities', vendor: 'Power Co.', payment: 'bank_transfer', status: 'paid' },
		{ date: '2026-01-25', amount: 275.00, desc: 'Hoof trimming - cattle', category: 'veterinary', speciesKey: 'Cattle', vendor: 'Dr. Martinez', payment: 'cash', qty: 4, qtyUnit: 'units', unitCost: 68.75, status: 'paid' },
		{ date: '2026-02-01', amount: 3200.00, desc: 'New water troughs', category: 'equipment', vendor: 'Farm Equipment Ltd.', payment: 'credit_card', qty: 4, qtyUnit: 'units', unitCost: 800.00, status: 'paid' },
		{ date: '2026-02-10', amount: 950.00, desc: 'Goat mineral supplements - bulk', category: 'feed', speciesKey: 'Goat', vendor: 'AgriSupply', payment: 'debit_card', qty: 50, qtyUnit: 'bags', unitCost: 19.00, status: 'paid' },
		{ date: '2026-02-15', amount: 600.00, desc: 'Veterinary checkup - pending invoice', category: 'veterinary', vendor: 'Dr. Martinez', payment: null, status: 'pending' },
		{ date: '2026-02-20', amount: 180.00, desc: 'Transport - vet visit pickup', category: 'transport', vendor: 'Rural Transport', payment: 'cash', status: 'paid' },
		{ date: '2026-03-01', amount: 2100.00, desc: 'March feed order', category: 'feed', vendor: 'FarmFeed Co.', payment: 'bank_transfer', qty: 700, qtyUnit: 'kg', unitCost: 3.00, status: 'pending' },
	];

	let expenseCount = 0;
	for (const e of expenseDefs) {
		const speciesId = e.speciesKey ? species[e.speciesKey] : null;
		await query(
			`INSERT INTO expenses (farm_id, date, amount, description, category, species_id, vendor, payment_method, invoice_number, quantity, quantity_unit, unit_cost, status, created_by, created_at, updated_at)
			 VALUES (:farmId, :date, :amount, :desc, :category, :speciesId, :vendor, :payment, NULL, :qty, :qtyUnit, :unitCost, :status, :userId, :now, :now)`,
			{
				farmId, date: e.date, amount: e.amount, desc: e.desc, category: e.category,
				speciesId, vendor: e.vendor || null, payment: e.payment || null,
				qty: e.qty || null, qtyUnit: e.qtyUnit || null, unitCost: e.unitCost || null,
				status: e.status, userId, now,
			},
		);
		expenseCount++;
	}
	console.log(`Created ${expenseCount} expenses`);

	// --- Flocks (Chicken) ---
	const chickenSpeciesId = species['Chicken'];
	const chickenBreeds = {};
	for (const [key, id] of Object.entries(breeds)) {
		if (key.startsWith('Chicken:')) {
			chickenBreeds[key.replace('Chicken:', '')] = id;
		}
	}

	const flockDefs = [
		{
			name: 'Layer Flock A',
			breedKey: 'Leghorn',
			flockType: 'layers',
			initialCount: 50,
			currentCount: 47,
			startDate: '2025-10-01',
			acquisitionType: 'purchased',
			houseName: 'Coop 1',
			ageAtAcquisitionWeeks: 18,
			notes: 'First batch of laying hens',
		},
		{
			name: 'Dual Purpose Flock B',
			breedKey: 'Rhode Island Red',
			flockType: 'dual_purpose',
			initialCount: 30,
			currentCount: 28,
			startDate: '2025-11-15',
			acquisitionType: 'purchased',
			houseName: 'Coop 2',
			ageAtAcquisitionWeeks: 16,
			notes: 'Mixed use flock for eggs and meat',
		},
	];

	const flockIds = [];
	for (const f of flockDefs) {
		const flock = await queryOne(
			`INSERT INTO flocks (farm_id, species_id, breed_id, name, flock_type, initial_count, current_count, status, start_date, acquisition_type, house_name, age_at_acquisition_weeks, notes, created_at, updated_at)
			 VALUES (:farmId, :speciesId, :breedId, :name, :flockType, :initialCount, :currentCount, 'active', :startDate, :acquisitionType, :houseName, :ageAtAcquisitionWeeks, :notes, :now, :now)
			 RETURNING id`,
			{
				farmId, speciesId: chickenSpeciesId, breedId: chickenBreeds[f.breedKey],
				name: f.name, flockType: f.flockType, initialCount: f.initialCount,
				currentCount: f.currentCount, startDate: f.startDate,
				acquisitionType: f.acquisitionType, houseName: f.houseName,
				ageAtAcquisitionWeeks: f.ageAtAcquisitionWeeks, notes: f.notes, now,
			},
		);
		flockIds.push({ id: flock.id, ...f });
	}
	console.log(`Created ${flockIds.length} flocks`);

	// --- Flock Events ---
	const flockEventDefs = [
		// Layer Flock A: 50 initial → -2 mortality → -1 cull = 47 current
		{ flockIdx: 0, eventType: 'mortality', count: 2, date: '2025-11-10', reason: 'Predator attack' },
		{ flockIdx: 0, eventType: 'cull', count: 1, date: '2025-12-05', reason: 'Sick hen, not recovering' },
		// Dual Purpose Flock B: 30 initial → -1 mortality → -1 sale = 28 current
		{ flockIdx: 1, eventType: 'mortality', count: 1, date: '2025-12-20', reason: 'Unknown cause' },
		{ flockIdx: 1, eventType: 'sale', count: 1, date: '2026-01-15', reason: 'Rooster sold to neighbor' },
	];

	for (const e of flockEventDefs) {
		await query(
			`INSERT INTO flock_events (flock_id, event_type, count, date, reason, recorded_by, created_at, updated_at)
			 VALUES (:flockId, :eventType, :count, :date, :reason, :userId, :now, :now)`,
			{
				flockId: flockIds[e.flockIdx].id, eventType: e.eventType,
				count: e.count, date: e.date, reason: e.reason, userId, now,
			},
		);
	}
	console.log(`Created ${flockEventDefs.length} flock events`);

	// --- Egg Collections ---
	// Generate 14 days of egg data for each flock
	const eggCollections = [];
	for (let daysAgo = 14; daysAgo >= 1; daysAgo--) {
		const date = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000)
			.toISOString().split('T')[0];

		// Layer Flock A: ~85-92% lay rate (47 hens)
		const flockAEggs = 40 + Math.floor(Math.random() * 4);
		const flockABroken = Math.random() < 0.3 ? Math.floor(Math.random() * 3) : 0;
		eggCollections.push({
			flockId: flockIds[0].id, date, totalEggs: flockAEggs,
			brokenEggs: flockABroken, notes: null,
		});

		// Dual Purpose Flock B: ~60-75% lay rate (28 hens)
		const flockBEggs = 17 + Math.floor(Math.random() * 4);
		const flockBBroken = Math.random() < 0.2 ? Math.floor(Math.random() * 2) : 0;
		eggCollections.push({
			flockId: flockIds[1].id, date, totalEggs: flockBEggs,
			brokenEggs: flockBBroken, notes: null,
		});
	}

	for (const ec of eggCollections) {
		await query(
			`INSERT INTO egg_collections (flock_id, date, total_eggs, broken_eggs, collected_by, notes, created_at, updated_at)
			 VALUES (:flockId, :date, :totalEggs, :brokenEggs, :userId, :notes, :now, :now)`,
			{ flockId: ec.flockId, date: ec.date, totalEggs: ec.totalEggs, brokenEggs: ec.brokenEggs, userId, notes: ec.notes, now },
		);
	}
	console.log(`Created ${eggCollections.length} egg collections`);

	console.log('\nDev seed complete!');
	console.log('Login: testuser@test.com / Password1');
}

main()
	.catch((err) => {
		console.error('Dev seed failed:', err);
		process.exit(1);
	})
	.finally(() => sequelize.close());
