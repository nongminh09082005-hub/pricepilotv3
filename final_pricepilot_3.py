from flask import Flask, request, render_template_string, redirect, url_for, session
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import json

app = Flask(__name__)
app.secret_key = "pricepilot-secret-key"

MATERIAL_PRICE = {
    "Thép": 29825172,
    "Inox": 84000000,
    "Nhôm": 93255906,
    "Đồng": 358625259
}

BUTTON_CSS = """
button, .btn {
    background: linear-gradient(135deg, #008735, #00b84a);
    color: white;
    border: none;
    padding: 15px 42px;
    font-size: 18px;
    font-weight: 700;
    border-radius: 14px;
    cursor: pointer;
    text-decoration: none;
    box-shadow: 0 8px 20px rgba(0, 204, 102, 0.28);
    transition: all 0.25s ease;
    display: inline-block;
}

button:hover, .btn:hover {
    background: linear-gradient(135deg, #00cc66, #00e676);
    transform: translateY(-3px);
    box-shadow: 0 12px 28px rgba(0, 204, 102, 0.45);
}

button:active, .btn:active {
    transform: translateY(0);
}

.detail {
    box-shadow: none !important;
}

.detail:hover {
    box-shadow: 0 8px 22px rgba(255,255,255,0.18) !important;
}
"""

INTRO_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>PricePilot</title>
<style>
body {
    margin: 0;
    font-family: Poppins, Arial, sans-serif;
    background: linear-gradient(rgba(15,23,42,.78), rgba(15,23,42,.88)),
                url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab');
    background-size: cover;
    background-position: center;
    color: white;
    min-height: 100vh;
}

.header {
    padding: 28px 60px;
    font-size: 28px;
    font-weight: 800;
}

.hero {
    min-height: calc(100vh - 100px);
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    flex-direction: column;
    padding: 40px;
}

.hero h1 {
    font-size: 76px;
    margin-bottom: 18px;
}

.hero p {
    font-size: 21px;
    max-width: 900px;
    line-height: 1.7;
    color: #e5e7eb;
}

.buttons {
    margin-top: 38px;
    display: flex;
    gap: 25px;
}

""" + BUTTON_CSS + """

.detail {
    background: transparent;
    border: 2px solid rgba(255,255,255,.8);
}

.detail:hover {
    background: white;
    color: #008735;
}

.modal {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.75);
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

.modal-content {
    background: #111827;
    color: white;
    width: 72%;
    max-height: 80vh;
    overflow-y: auto;
    padding: 38px;
    border-radius: 18px;
    line-height: 1.75;
    border: 1px solid rgba(255,255,255,.12);
    box-shadow: 0 25px 70px rgba(0,0,0,.45);
}

.modal-content h2 {
    margin-top: 0;
    font-size: 32px;
}

.modal-content h3 {
    color: #00cc66;
    margin-top: 26px;
}

.close {
    float: right;
    font-size: 30px;
    cursor: pointer;
    font-weight: bold;
}

@media (max-width: 768px) {
    .hero h1 { font-size: 48px; }
    .buttons { flex-direction: column; }
    .modal-content { width: 86%; }
}
</style>
</head>

<body>
<div class="header">PricePilot</div>

<section class="hero">
    <h1>PricePilot</h1>
    <p>
        PricePilot supports SME mechanical manufacturing businesses in pricing decisions.
        The tool uses historical price-demand data to calculate fixed elasticity, then applies
        Monte Carlo simulation to estimate demand, cost, profit, and risk under different price increases.
    </p>

    <div class="buttons">
        <a class="btn" href="/input">Start</a>
        <button class="detail" onclick="openModal()">Detail</button>
    </div>
</section>

<div class="modal" id="detailModal">
    <div class="modal-content">
        <span class="close" onclick="closeModal()">&times;</span>

        <h2>How PricePilot Works</h2>

        <p>
        PricePilot uses an <b>elasticity-based demand model</b>. Price increase is the firm's decision variable,
        elasticity is calculated from historical price-demand data, and market conditions are simulated as uncertain variables.
        </p>

        <h3>1. Cost Structure</h3>
        <p>
        The system calculates monthly material cost, waste-adjusted material cost,
        labor cost, electricity/rent, maintenance, depreciation, and total monthly cost.
        </p>

        <h3>2. Fixed Elasticity from Historical Data</h3>
        <p>
        Elasticity is calculated as the absolute percentage change in demand divided by the absolute percentage change in price.
        This means the model does not randomly guess elasticity. It is estimated from the firm's own historical data.
        </p>

        <h3>3. Monte Carlo Simulation</h3>
        <p>
        For each candidate price increase, Monte Carlo randomizes market growth, customer budget pressure,
        material shock impact, and material inflation. The system then estimates new demand, new cost per order,
        profit, and risk.
        </p>
    </div>
</div>

<script>
function openModal() {
    document.getElementById("detailModal").style.display = "flex";
}
function closeModal() {
    document.getElementById("detailModal").style.display = "none";
}
</script>

</body>
</html>
"""

INPUT_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>PricePilot Input</title>
<style>
body {
    font-family: Poppins, Arial, sans-serif;
    margin: 0;
    background: linear-gradient(135deg, #0f172a, #111827);
    color: white;
    min-height: 100vh;
}

.container {
    max-width: 1000px;
    margin: auto;
    padding: 45px 30px;
}

.back {
    color: #00cc66;
    text-decoration: none;
    font-weight: 700;
}

.card {
    background: rgba(255,255,255,0.06);
    padding: 35px;
    border-radius: 22px;
    margin: 30px 0;
    box-shadow: 0 20px 45px rgba(0,0,0,0.25);
    border: 1px solid rgba(255,255,255,0.1);
    backdrop-filter: blur(12px);
}

h1 {
    font-size: 42px;
    margin-bottom: 8px;
}

.subtitle {
    color: #cbd5e1;
    margin-bottom: 30px;
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 22px;
}

.section-title {
    grid-column: 1 / -1;
    color: #00cc66;
    font-size: 22px;
    font-weight: 800;
    margin-top: 18px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.15);
}

.form-group {
    display: flex;
    flex-direction: column;
}

label {
    font-weight: 600;
    margin-bottom: 8px;
}

input, select {
    padding: 13px 15px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.14);
    background: rgba(255,255,255,0.08);
    color: white;
    font-size: 15px;
    outline: none;
}

select {
    appearance: none;
    background:
        linear-gradient(45deg, transparent 50%, #e5e7eb 50%),
        linear-gradient(135deg, #e5e7eb 50%, transparent 50%),
        rgba(255,255,255,0.08);
    background-position:
        calc(100% - 22px) calc(50% - 3px),
        calc(100% - 16px) calc(50% - 3px),
        0 0;
    background-size:
        6px 6px,
        6px 6px,
        100% 100%;
    background-repeat: no-repeat;
}

select option {
    background: #1f2937;
    color: white;
    padding: 14px;
}

input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

input[type="number"] {
    appearance: textfield;
    -moz-appearance: textfield;
}

input[type="range"] {
    accent-color: #00cc66;
    padding: 0;
    cursor: pointer;
}

.money-input {
    text-align: left;
}

.range-value {
    color: #00cc66;
    font-weight: 800;
    margin-top: 8px;
}

small {
    color: #cbd5e1;
    margin-top: 8px;
    line-height: 1.5;
}

.range-card {
    background: rgba(255,255,255,0.055);
    padding: 18px 18px 16px;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.12);
}

.dual-slider {
    position: relative;
    height: 42px;
    margin-top: 12px;
}

.slider-track-bg {
    position: absolute;
    top: 18px;
    left: 0;
    right: 0;
    height: 5px;
    border-radius: 999px;
    background: rgba(255,255,255,0.25);
}

.slider-track-fill {
    position: absolute;
    top: 18px;
    height: 5px;
    border-radius: 999px;
    background: linear-gradient(90deg, #00cc66, #7dd3fc);
}

.dual-slider input[type="range"] {
    position: absolute;
    top: 8px;
    left: 0;
    width: 100%;
    height: 24px;
    background: none;
    pointer-events: none;
    appearance: none;
    -webkit-appearance: none;
}

.dual-slider input[type="range"]::-webkit-slider-runnable-track {
    height: 5px;
    background: transparent;
}

.dual-slider input[type="range"]::-webkit-slider-thumb {
    pointer-events: auto;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #f8fafc;
    border: 3px solid #7dd3fc;
    box-shadow: 0 0 0 4px rgba(125,211,252,0.18), 0 6px 18px rgba(0,0,0,0.35);
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    margin-top: -8px;
}

.dual-slider input[type="range"]::-moz-range-thumb {
    pointer-events: auto;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #f8fafc;
    border: 3px solid #7dd3fc;
    box-shadow: 0 0 0 4px rgba(125,211,252,0.18), 0 6px 18px rgba(0,0,0,0.35);
    cursor: pointer;
}

.dual-label-row {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
    color: #e5e7eb;
    font-weight: 800;
}

.dual-label-row span {
    color: #00cc66;
    font-size: 18px;
}

.dual-label-row small {
    display: block;
    color: #cbd5e1;
    font-size: 13px;
    margin-top: 2px;
}

.button-wrap {
    text-align: center;
    margin-top: 35px;
}

""" + BUTTON_CSS + """

@media (max-width: 768px) {
    .form-grid {
        grid-template-columns: 1fr;
    }
}
</style>
</head>

<body>
<div class="container">

<a class="back" href="/">← Back to intro</a>

<div class="card">
    <h1>PricePilot Input</h1>
    <p class="subtitle">
        Enter cost data, current demand, historical price-demand data, and market uncertainty ranges to run Monte Carlo simulation.
    </p>

    <form method="POST" action="/run">
        <div class="form-grid">

            <div class="section-title">1. Monthly Cost Inputs</div>

            <div class="form-group">
                <label>Material type</label>
                <select name="material">
                    <option value="Thép">Steel - 29,825,172 VND/ton</option>
                    <option value="Inox">Stainless steel - 84,000,000 VND/ton</option>
                    <option value="Nhôm">Aluminum - 93,255,906 VND/ton</option>
                    <option value="Đồng">Copper - 358,625,259 VND/ton</option>
                </select>
            </div>

            <div class="form-group">
                <label>Tons per month</label>
                <input type="number" name="tons" value="120">
            </div>

            <div class="form-group">
                <label>Waste rate %</label>
                <input type="range" name="waste_rate" min="0" max="20" value="5" oninput="wasteVal.innerText=this.value">
                <span class="range-value"><span id="wasteVal">5</span>%</span>
            </div>

            <div class="form-group">
                <label>Number of workers</label>
                <input type="number" name="workers" value="25">
            </div>

            <div class="form-group">
                <label>Monthly salary per worker VND</label>
                <input class="money-input" type="text" name="salary" value="9,000,000">
            </div>

            <div class="form-group">
                <label>Electricity and rent per year VND</label>
                <input class="money-input" type="text" name="electricity_year" value="600,000,000">
            </div>

            <div class="form-group">
                <label>Maintenance cost per year VND</label>
                <input class="money-input" type="text" name="maintenance_year" value="300,000,000">
            </div>

            <div class="form-group">
                <label>Machine value VND</label>
                <input class="money-input" type="text" name="machine_value" value="3,000,000,000">
            </div>

            <div class="form-group">
                <label>Machine life years</label>
                <input type="number" name="machine_life" value="8">
            </div>

            <div class="section-title">2. Business Baseline Inputs</div>

            <div class="form-group">
                <label>Base demand / current monthly orders</label>
                <input type="number" name="base_demand" value="45">
                <small>Current average monthly orders used as the baseline demand.</small>
            </div>

            <div class="form-group">
                <label>Target margin %</label>
                <input type="range" name="margin" min="0" max="50" value="20" oninput="marginVal.innerText=this.value">
                <span class="range-value"><span id="marginVal">20</span>%</span>
            </div>

            <div class="section-title">3. Historical Data for Fixed Elasticity</div>

            <div class="form-group">
                <label>Old selling price VND/order</label>
                <input class="money-input" type="text" name="old_price" value="100,000,000">
                <small>Historical selling price before the price change.</small>
            </div>

            <div class="form-group">
                <label>New selling price VND/order</label>
                <input class="money-input" type="text" name="new_price_history" value="110,000,000">
                <small>Historical selling price after the price change.</small>
            </div>

            <div class="form-group">
                <label>Old demand / orders</label>
                <input type="number" name="old_demand" value="50">
                <small>Monthly demand before the historical price change.</small>
            </div>

            <div class="form-group">
                <label>New demand / orders</label>
                <input type="number" name="new_demand_history" value="42">
                <small>Monthly demand after the historical price change.</small>
            </div>

            <div class="section-title">4. Market Uncertainty Ranges</div>

            <div class="form-group range-card">
                <label>Market growth range %</label>
                <input type="hidden" name="market_growth_min" id="market_growth_min" value="0">
                <input type="hidden" name="market_growth_max" id="market_growth_max" value="5">

                <div class="dual-slider">
                    <div class="slider-track-bg"></div>
                    <div class="slider-track-fill" id="market_growth_fill"></div>

                    <input type="range" id="market_growth_low" min="-10" max="15" value="0"
                           oninput="updateDualRange('market_growth', '%', this)">
                    <input type="range" id="market_growth_high" min="-10" max="15" value="5"
                           oninput="updateDualRange('market_growth', '%', this)">
                </div>

                <div class="dual-label-row">
                    <div>
                        <small>Min</small>
                        <span id="market_growth_low_label">0%</span>
                    </div>
                    <div>
                        <small>Max</small>
                        <span id="market_growth_high_label">5%</span>
                    </div>
                </div>

                <small>Positive demand change from market or industry growth.</small>
            </div>

            <div class="form-group range-card">
                <label>Customer budget pressure range %</label>
                <input type="hidden" name="budget_pressure_min" id="budget_pressure_min" value="1">
                <input type="hidden" name="budget_pressure_max" id="budget_pressure_max" value="5">

                <div class="dual-slider">
                    <div class="slider-track-bg"></div>
                    <div class="slider-track-fill" id="budget_pressure_fill"></div>

                    <input type="range" id="budget_pressure_low" min="0" max="20" value="1"
                           oninput="updateDualRange('budget_pressure', '%', this)">
                    <input type="range" id="budget_pressure_high" min="0" max="20" value="5"
                           oninput="updateDualRange('budget_pressure', '%', this)">
                </div>

                <div class="dual-label-row">
                    <div>
                        <small>Min</small>
                        <span id="budget_pressure_low_label">1%</span>
                    </div>
                    <div>
                        <small>Max</small>
                        <span id="budget_pressure_high_label">5%</span>
                    </div>
                </div>

                <small>Negative demand pressure caused by tighter customer budgets.</small>
            </div>

            <div class="form-group range-card">
                <label>Material shock impact range %</label>
                <input type="hidden" name="material_shock_min" id="material_shock_min" value="1">
                <input type="hidden" name="material_shock_max" id="material_shock_max" value="4">

                <div class="dual-slider">
                    <div class="slider-track-bg"></div>
                    <div class="slider-track-fill" id="material_shock_fill"></div>

                    <input type="range" id="material_shock_low" min="0" max="20" value="1"
                           oninput="updateDualRange('material_shock', '%', this)">
                    <input type="range" id="material_shock_high" min="0" max="20" value="4"
                           oninput="updateDualRange('material_shock', '%', this)">
                </div>

                <div class="dual-label-row">
                    <div>
                        <small>Min</small>
                        <span id="material_shock_low_label">1%</span>
                    </div>
                    <div>
                        <small>Max</small>
                        <span id="material_shock_high_label">4%</span>
                    </div>
                </div>

                <small>Demand reduction caused by material price volatility or customer delay.</small>
            </div>

            <div class="form-group range-card">
                <label>Material inflation range %</label>
                <input type="hidden" name="material_inflation_min" id="material_inflation_min" value="3">
                <input type="hidden" name="material_inflation_max" id="material_inflation_max" value="10">

                <div class="dual-slider">
                    <div class="slider-track-bg"></div>
                    <div class="slider-track-fill" id="material_inflation_fill"></div>

                    <input type="range" id="material_inflation_low" min="0" max="20" value="3"
                           oninput="updateDualRange('material_inflation', '%', this)">
                    <input type="range" id="material_inflation_high" min="0" max="20" value="10"
                           oninput="updateDualRange('material_inflation', '%', this)">
                </div>

                <div class="dual-label-row">
                    <div>
                        <small>Min</small>
                        <span id="material_inflation_low_label">3%</span>
                    </div>
                    <div>
                        <small>Max</small>
                        <span id="material_inflation_high_label">10%</span>
                    </div>
                </div>

                <small>Cost increase from material price inflation.</small>
            </div>

            <div class="section-title">5. Price Decision and Simulation Settings</div>

            <div class="form-group">
                <label>Maximum price increase to test %</label>
                <input type="range" name="max_price_increase" min="1" max="30" value="20" oninput="maxIncVal.innerText=this.value">
                <span class="range-value"><span id="maxIncVal">20</span>%</span>
                <small>Price increase is a decision variable. It is tested across the selected range, not randomized.</small>
            </div>

            <div class="form-group">
                <label>Monte Carlo simulations per price level</label>
                <select name="n_simulations">
                    <option value="500">500 simulations</option>
                    <option value="1000" selected>1,000 simulations</option>
                    <option value="3000">3,000 simulations</option>
                </select>
            </div>

        </div>

        <div class="button-wrap">
            <button type="submit">Run</button>
        </div>
    </form>
</div>

</div>

<script>
function formatNumberWithCommas(value) {
    value = value.replace(/,/g, "");
    if (value === "" || isNaN(value)) return "";
    return Number(value).toLocaleString("en-US");
}

document.querySelectorAll(".money-input").forEach(function(input) {
    input.addEventListener("input", function() {
        const cursorPosition = input.selectionStart;
        const oldLength = input.value.length;

        input.value = formatNumberWithCommas(input.value);

        const newLength = input.value.length;
        const newPosition = Math.max(0, cursorPosition + (newLength - oldLength));
        input.setSelectionRange(newPosition, newPosition);
    });
});

document.querySelector("form").addEventListener("submit", function() {
    document.querySelectorAll(".money-input").forEach(function(input) {
        input.value = input.value.replace(/,/g, "");
    });
});

function updateDualRange(prefix, suffix, activeInput) {
    const low = document.getElementById(prefix + "_low");
    const high = document.getElementById(prefix + "_high");
    const fill = document.getElementById(prefix + "_fill");

    const min = Number(low.min);
    const max = Number(low.max);

    let lowVal = Number(low.value);
    let highVal = Number(high.value);

    if (lowVal > highVal) {
        if (activeInput && activeInput.id.endsWith("_low")) {
            low.value = highVal;
            lowVal = highVal;
        } else {
            high.value = lowVal;
            highVal = lowVal;
        }
    }

    const leftPercent = ((lowVal - min) / (max - min)) * 100;
    const rightPercent = ((highVal - min) / (max - min)) * 100;

    fill.style.left = leftPercent + "%";
    fill.style.width = (rightPercent - leftPercent) + "%";

    document.getElementById(prefix + "_min").value = lowVal;
    document.getElementById(prefix + "_max").value = highVal;

    document.getElementById(prefix + "_low_label").innerText = lowVal + suffix;
    document.getElementById(prefix + "_high_label").innerText = highVal + suffix;
}

window.addEventListener("load", function() {
    updateDualRange("market_growth", "%");
    updateDualRange("budget_pressure", "%");
    updateDualRange("material_shock", "%");
    updateDualRange("material_inflation", "%");
});
</script>

</body>
</html>
"""

LOADING_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Loading...</title>
<style>
body {
    margin: 0;
    font-family: Poppins, Arial, sans-serif;
    background: #0f172a;
    color: white;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}

.loader {
    width: 90px;
    height: 90px;
    border: 10px solid rgba(255,255,255,.2);
    border-top: 10px solid #00cc66;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

h1 {
    margin-top: 30px;
}

.progress {
    margin-top: 25px;
    width: 380px;
    height: 12px;
    background: rgba(255,255,255,.2);
    border-radius: 20px;
    overflow: hidden;
}

.bar {
    height: 100%;
    width: 0;
    background: #00cc66;
    animation: loading 5s forwards;
}

@keyframes loading {
    to { width: 100%; }
}
</style>
</head>

<body>

<div class="loader"></div>
<h1>Running elasticity-based Monte Carlo simulation...</h1>
<p>Randomizing market conditions and estimating demand, cost, profit, and risk...</p>

<div class="progress">
    <div class="bar"></div>
</div>

<script>
setTimeout(function() {
    window.location.href = "/result";
}, 5000);
</script>

</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>PricePilot Result</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
:root {
    --bg: #08111f;
    --panel: rgba(15, 28, 49, 0.86);
    --panel-2: rgba(18, 34, 58, 0.72);
    --panel-3: rgba(255,255,255,0.055);
    --line: rgba(148, 163, 184, 0.18);
    --line-strong: rgba(0, 204, 102, 0.42);
    --green: #00cc66;
    --green-2: #26e889;
    --blue: #38bdf8;
    --text: #f8fafc;
    --muted: #9ca3af;
    --muted-2: #cbd5e1;
    --warning: #fbbf24;
    --danger: #fb7185;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Poppins, Inter, Arial, sans-serif;
    color: var(--text);
    background:
        radial-gradient(circle at 8% 0%, rgba(0, 204, 102, 0.16), transparent 34%),
        radial-gradient(circle at 92% 8%, rgba(56, 189, 248, 0.13), transparent 28%),
        linear-gradient(135deg, #071020 0%, #0f172a 50%, #08111f 100%);
    min-height: 100vh;
}

.dashboard-shell {
    width: min(1540px, calc(100% - 44px));
    margin: 0 auto;
    padding: 32px 0 46px;
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 18px;
}

.brand-row { display: flex; align-items: center; gap: 14px; min-width: 0; }
.logo-mark {
    width: 42px;
    height: 42px;
    border-radius: 13px;
    display: grid;
    place-items: center;
    color: var(--green-2);
    background: linear-gradient(135deg, rgba(0,204,102,0.22), rgba(56,189,248,0.10));
    border: 1px solid rgba(0,204,102,0.28);
    box-shadow: 0 0 28px rgba(0,204,102,0.18);
    font-size: 23px;
    flex: 0 0 auto;
}

.title-wrap { min-width: 0; }
.title-wrap h1 {
    margin: 0;
    font-size: clamp(28px, 3vw, 42px);
    line-height: 1.05;
    letter-spacing: -0.04em;
}
.title-wrap p {
    margin: 8px 0 0;
    color: var(--muted-2);
    font-size: 14px;
}

.top-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.pill-btn, .ghost-btn {
    border: 1px solid var(--line);
    background: rgba(255,255,255,0.055);
    color: var(--text);
    border-radius: 14px;
    padding: 12px 15px;
    font-size: 13px;
    font-weight: 700;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 9px;
    white-space: nowrap;
    box-shadow: none;
}
.pill-btn:hover, .ghost-btn:hover { transform: translateY(-1px); border-color: rgba(0,204,102,0.45); }

.main-grid {
    display: grid;
    grid-template-columns: 1.32fr 0.9fr;
    gap: 18px;
    align-items: stretch;
}

.card {
    background: linear-gradient(180deg, rgba(20, 36, 61, 0.78), rgba(10, 22, 39, 0.82));
    border: 1px solid var(--line);
    border-radius: 22px;
    box-shadow: 0 22px 70px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
    overflow: hidden;
}

.hero-card {
    padding: 24px;
    position: relative;
    min-height: 238px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.hero-card::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(90deg, rgba(0,204,102,0.13), transparent 52%),
        radial-gradient(circle at 20% 50%, rgba(0,204,102,0.22), transparent 26%);
    pointer-events: none;
}
.hero-content { position: relative; z-index: 1; display: grid; grid-template-columns: 110px 1fr; gap: 22px; align-items: center; }
.target-ring {
    width: 96px; height: 96px; border-radius: 50%;
    display: grid; place-items: center;
    background: radial-gradient(circle, rgba(0,204,102,0.22), rgba(0,204,102,0.04));
    border: 1px solid rgba(0,204,102,0.35);
    box-shadow: 0 0 40px rgba(0,204,102,0.22);
    font-size: 46px;
}
.eyebrow { color: var(--green-2); font-weight: 900; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; }
.hero-card h2 { margin: 8px 0 8px; font-size: clamp(28px, 4vw, 46px); line-height: 1.02; letter-spacing: -0.04em; }
.hero-card h2 span { color: var(--green-2); }
.hero-card p { color: var(--muted-2); line-height: 1.55; margin: 0; max-width: 620px; }
.hero-metrics {
    position: relative; z-index: 1;
    margin-top: 22px;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
}
.hero-mini {
    padding: 16px;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px;
    background: rgba(255,255,255,0.045);
    min-width: 0;
}
.hero-mini .label, .kpi-label, .strategy-label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; font-weight: 800; }
.hero-mini .value { margin-top: 7px; color: var(--green-2); font-size: clamp(17px, 1.65vw, 23px); font-weight: 900; line-height: 1.15; overflow-wrap: anywhere; }
.hero-mini .sub { margin-top: 4px; color: var(--muted-2); font-size: 12px; }

.recommendation-card {
    padding: 24px;
    border-color: rgba(0,204,102,0.38);
    background:
        radial-gradient(circle at 15% 20%, rgba(0,204,102,0.22), transparent 30%),
        linear-gradient(180deg, rgba(15, 40, 42, 0.82), rgba(10, 22, 39, 0.90));
    min-height: 238px;
}
.rec-head { display: flex; gap: 16px; align-items: flex-start; }
.rec-icon {
    width: 54px; height: 54px; border-radius: 50%;
    display: grid; place-items: center;
    background: rgba(0,204,102,0.15);
    border: 1px solid rgba(0,204,102,0.42);
    color: var(--green-2); font-size: 29px;
    flex: 0 0 auto;
}
.recommendation-card h2 { margin: 4px 0 8px; font-size: clamp(22px, 2.6vw, 34px); line-height: 1.08; letter-spacing: -0.03em; }
.recommendation-card h2 span { color: var(--green-2); }
.rec-separator { height: 1px; background: var(--line); margin: 22px 0; }
.rec-stats { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 18px; }
.rec-stat { min-width: 0; }
.rec-stat .big { color: var(--green-2); font-weight: 900; font-size: clamp(19px, 2vw, 28px); line-height: 1.15; overflow-wrap: anywhere; margin-top: 6px; }
.rec-stat .small { color: var(--muted-2); font-size: 12px; margin-top: 4px; }
.confidence-strip {
    margin-top: 18px; padding: 13px 14px; border-radius: 14px;
    background: rgba(0,204,102,0.08); border: 1px solid rgba(0,204,102,0.18);
    color: var(--green-2); font-size: 13px; font-weight: 800;
}

.section-title {
    margin: 26px 0 14px;
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.section-title h2 { font-size: 18px; margin: 0; letter-spacing: -0.02em; }
.section-title .hint { color: var(--muted); font-size: 12px; }

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 12px;
}
.kpi-card {
    min-width: 0;
    padding: 16px;
    display: grid;
    grid-template-columns: 42px minmax(0,1fr);
    gap: 12px;
    align-items: center;
}
.kpi-icon {
    width: 42px; height: 42px; border-radius: 14px;
    display: grid; place-items: center;
    background: rgba(148,163,184,0.10);
    border: 1px solid rgba(148,163,184,0.13);
    color: var(--green-2); font-size: 20px;
}
.kpi-value {
    color: var(--green-2);
    font-weight: 900;
    font-size: clamp(16px, 1.45vw, 23px);
    line-height: 1.16;
    overflow-wrap: anywhere;
    word-break: break-word;
}
.kpi-sub { color: var(--muted-2); font-size: 11px; margin-top: 4px; }

.analytics-grid {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 16px;
}
.chart-card { padding: 18px; min-width: 0; }
.chart-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 8px; }
.chart-head h3 { margin: 0; font-size: 16px; }
.chart-head p { margin: 5px 0 0; color: var(--muted); font-size: 12px; }
.chart-wrap { min-height: 320px; overflow: hidden; border-radius: 14px; }
.distribution-launch {
    min-height: 320px;
    cursor: pointer;
    position: relative;
    display: flex; flex-direction: column; justify-content: space-between;
    transition: transform .18s ease, border-color .18s ease, background .18s ease;
}
.distribution-launch:hover { transform: translateY(-3px); border-color: rgba(0,204,102,0.48); background: linear-gradient(180deg, rgba(17,48,58,0.86), rgba(10,22,39,0.88)); }
.distribution-visual {
    height: 145px;
    margin-top: 16px;
    display: flex; align-items: end; gap: 7px;
    padding: 12px 4px 0;
}
.bar-demo { flex: 1; min-width: 5px; border-radius: 999px 999px 0 0; background: linear-gradient(180deg, var(--green-2), rgba(0,204,102,0.18)); opacity: .86; }
.open-badge {
    margin-top: 16px;
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; padding: 13px 14px; border-radius: 14px;
    background: rgba(0,204,102,0.13); border: 1px solid rgba(0,204,102,0.24);
    color: var(--green-2); font-weight: 900; font-size: 13px;
}

.strategy-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0,1fr));
    gap: 14px;
}
.strategy-card {
    padding: 18px;
    min-width: 0;
    position: relative;
    isolation: isolate;
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}
.strategy-card:hover { transform: translateY(-2px); }
.strategy-card::before {
    content: "";
    position: absolute;
    inset: 0;
    opacity: .78;
    pointer-events: none;
    z-index: -1;
}
.strategy-card.recommended { box-shadow: 0 0 0 1px rgba(251,191,36,0.18), 0 18px 48px rgba(0,0,0,.32); }
.strategy-card.aggressive-card { border-color: rgba(248,113,113,0.42); }
.strategy-card.aggressive-card::before { background: radial-gradient(circle at 0% 0%, rgba(239,68,68,0.22), transparent 38%), linear-gradient(180deg, rgba(64,20,28,0.46), rgba(10,22,39,0.34)); }
.strategy-card.balanced-card { border-color: rgba(251,191,36,0.52); }
.strategy-card.balanced-card::before { background: radial-gradient(circle at 0% 0%, rgba(251,191,36,0.23), transparent 38%), linear-gradient(180deg, rgba(65,48,13,0.38), rgba(10,22,39,0.36)); }
.strategy-card.conservative-card { border-color: rgba(0,204,102,0.34); }
.strategy-card.conservative-card::before { background: radial-gradient(circle at 0% 0%, rgba(0,204,102,0.16), transparent 36%), linear-gradient(180deg, rgba(10,48,34,0.24), rgba(10,22,39,0.34)); }
.strategy-top { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.strategy-name { display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 900; min-width: 0; }
.strategy-icon { width: 42px; height: 42px; border-radius: 14px; display: grid; place-items: center; background: rgba(0,204,102,0.12); color: var(--green-2); border: 1px solid rgba(0,204,102,0.18); flex: 0 0 auto; }
.aggressive-card .strategy-icon { background: rgba(239,68,68,0.14); color: #fb7185; border-color: rgba(248,113,113,0.26); }
.balanced-card .strategy-icon { background: rgba(251,191,36,0.16); color: #fbbf24; border-color: rgba(251,191,36,0.30); }
.conservative-card .strategy-icon { background: rgba(0,204,102,0.12); color: var(--green-2); border-color: rgba(0,204,102,0.20); }
.tag { font-size: 11px; border-radius: 999px; padding: 6px 9px; background: rgba(148,163,184,0.11); color: var(--muted-2); font-weight: 900; white-space: nowrap; }
.tag.green { color: var(--green-2); background: rgba(0,204,102,0.13); border: 1px solid rgba(0,204,102,0.19); }
.tag.yellow { color: var(--warning); background: rgba(251,191,36,0.14); border: 1px solid rgba(251,191,36,0.24); }
.tag.red { color: #fecaca; background: rgba(239,68,68,0.16); border: 1px solid rgba(248,113,113,0.24); }
.strategy-range { font-size: clamp(28px, 3vw, 42px); line-height: 1; letter-spacing: -0.04em; font-weight: 950; margin: 18px 0 8px; overflow-wrap:anywhere; }
.aggressive-card .strategy-range, .aggressive-card .strategy-stat strong { color: #fb7185; }
.balanced-card .strategy-range, .balanced-card .strategy-stat strong { color: #fbbf24; }
.conservative-card .strategy-range, .conservative-card .strategy-stat strong { color: var(--green-2); }
.strategy-meta { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 10px; margin-top: 16px; }
.strategy-stat { border-top: 1px solid var(--line); padding-top: 10px; min-width: 0; }
.strategy-stat strong { display:block; overflow-wrap:anywhere; font-size: clamp(13px, 1.05vw, 17px); line-height:1.25; }
.strategy-stat span { color: var(--muted); font-size: 11px; }
.strategy-details {
    margin-top: 14px;
    font-size: 12px;
    color: var(--muted-2);
    line-height: 1.58;
    max-height: 112px;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 0 8px 0 0;
    scrollbar-width: thin;
}
.aggressive-card .strategy-details { scrollbar-color: rgba(248,113,113,.65) rgba(255,255,255,.06); }
.balanced-card .strategy-details { scrollbar-color: rgba(251,191,36,.75) rgba(255,255,255,.06); }
.conservative-card .strategy-details { scrollbar-color: rgba(0,204,102,.65) rgba(255,255,255,.06); }
.strategy-details::-webkit-scrollbar { width: 7px; }
.strategy-details::-webkit-scrollbar-track { background: rgba(255,255,255,.055); border-radius: 999px; }
.strategy-details::-webkit-scrollbar-thumb { border-radius: 999px; border: 2px solid rgba(15,23,42,.70); }
.aggressive-card .strategy-details::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #fb7185, #dc2626); }
.balanced-card .strategy-details::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #fbbf24, #d97706); }
.conservative-card .strategy-details::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #26e889, #008735); }
.strategy-details .strategy-metrics { display: none; }
.strategy-details p { margin: 0 0 8px; }

.bottom-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
}
.insights-card { padding: 18px; }
.insight-row {
    display: grid;
    grid-template-columns: repeat(5, minmax(0,1fr));
    gap: 12px;
}
.insight-item {
    padding: 16px;
    border-radius: 16px;
    border: 1px solid var(--line);
    background: rgba(255,255,255,0.04);
    min-width: 0;
}
.insight-item .icon { color: var(--green-2); font-size: 24px; margin-bottom: 10px; }
.insight-item h4 { margin: 0 0 6px; color: var(--green-2); font-size: 13px; }
.insight-item p { margin: 0; color: var(--muted-2); font-size: 12px; line-height: 1.5; overflow-wrap: anywhere; }

.analysis-card { padding: 18px; }
.analysis-actions { display:flex; align-items:center; gap:12px; flex-wrap: wrap; margin-top: 12px; }
.action-btn {
    border: 1px solid rgba(0,204,102,0.28);
    background: rgba(0,204,102,0.12);
    color: var(--green-2);
    border-radius: 14px;
    padding: 13px 16px;
    font-weight: 900;
    cursor: pointer;
    box-shadow: none;
    font-size: 13px;
}
.action-btn:hover { transform: translateY(-1px); background: rgba(0,204,102,0.18); }
.try-btn { border-color: rgba(239,68,68,0.35); background: rgba(239,68,68,0.14); color: #fecaca; }

.insight-box {
    display: none;
    margin-top: 18px;
    color: var(--muted-2);
    line-height: 1.7;
}
.insight-box h2, .insight-box h3 { color: var(--text); }
.insight-box h3 { color: var(--green-2); }
.personalized-block {
    background: rgba(255,255,255,0.045);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 16px 18px;
    margin: 14px 0;
}
.personalized-block ul { margin-top: 8px; padding-left: 22px; }
.personalized-block li { margin-bottom: 8px; }
.insight-score-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-top: 12px;
}
.insight-score-grid div {
    padding: 14px 15px;
    border-radius: 15px;
    background: rgba(0,204,102,0.065);
    border: 1px solid rgba(0,204,102,0.12);
    min-width: 0;
}
.insight-score-grid span {
    display: block;
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .06em;
    font-weight: 900;
}
.insight-score-grid b {
    display: block;
    color: var(--green-2);
    font-size: clamp(18px, 2vw, 27px);
    margin: 6px 0 3px;
    overflow-wrap: anywhere;
}
.insight-score-grid small {
    color: var(--muted-2);
    line-height: 1.4;
}

.modal-overlay {
    position: fixed; inset: 0; display: none; align-items: center; justify-content: center;
    background: rgba(2, 6, 23, 0.78);
    backdrop-filter: blur(10px);
    z-index: 9999;
    padding: 24px;
}
.modal-window {
    width: min(1100px, 100%);
    max-height: 90vh;
    overflow: auto;
    border-radius: 26px;
    background: linear-gradient(180deg, rgba(16,30,52,0.98), rgba(8,17,31,0.98));
    border: 1px solid rgba(148,163,184,0.22);
    box-shadow: 0 28px 100px rgba(0,0,0,0.58);
    padding: 22px;
}
.modal-head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom: 16px; }
.modal-head h2 { margin:0; font-size: 24px; }
.modal-head p { margin:7px 0 0; color:var(--muted-2); font-size: 13px; }
.close-btn {
    width: 42px; height: 42px; border-radius: 50%;
    border: 1px solid var(--line);
    background: rgba(255,255,255,0.05);
    color: white; font-size: 22px; cursor:pointer;
}
.modal-controls {
    display:grid;
    grid-template-columns: 260px repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 16px;
}
.modal-select, .modal-stat {
    border: 1px solid var(--line);
    background: rgba(255,255,255,0.045);
    border-radius: 16px;
    padding: 13px 14px;
    min-width: 0;
}
.modal-select label, .modal-stat span { display:block; color:var(--muted); font-size: 11px; text-transform: uppercase; font-weight:900; letter-spacing:.06em; margin-bottom:5px; }
.modal-select select {
    width: 100%; padding: 12px 10px; border-radius: 12px;
    background: #0f172a; color:white; border: 1px solid var(--line);
    outline:none;
}
.modal-stat strong { display:block; color:var(--green-2); font-size: clamp(16px,1.5vw,23px); overflow-wrap:anywhere; }
#modalDistributionChart { min-height: 430px; }
.modal-note { color:var(--muted-2); font-size:13px; line-height:1.6; border-left: 4px solid var(--green); background:rgba(255,255,255,0.04); border-radius:12px; padding:12px 14px; margin-top: 12px; }

@media (max-width: 1200px) {
    .main-grid, .analytics-grid { grid-template-columns: 1fr; }
    .kpi-grid { grid-template-columns: repeat(3, minmax(0,1fr)); }
    .insight-row { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
@media (max-width: 850px) {
    .dashboard-shell { width: min(100% - 24px, 1540px); padding-top: 20px; }
    .topbar { align-items:flex-start; flex-direction:column; }
    .hero-content { grid-template-columns: 1fr; }
    .hero-metrics, .rec-stats, .strategy-grid, .modal-controls { grid-template-columns: 1fr; }
    .kpi-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
@media (max-width: 560px) {
    .kpi-grid, .insight-row { grid-template-columns: 1fr; }
    .hero-card, .recommendation-card, .card { border-radius: 18px; }
}
</style>
</head>

<body>
<div class="dashboard-shell">

    <div class="topbar">
        <div class="brand-row">
            <div class="logo-mark">▰</div>
            <div class="title-wrap">
                <h1>PricePilot Result</h1>
                <p>Personalized pricing dashboard based on elasticity and Monte Carlo simulation</p>
            </div>
        </div>
        <div class="top-actions">
            <div class="pill-btn">📅 Analysis session</div>
            <a class="ghost-btn" href="/input">↻ Run again</a>
            <button class="pill-btn" onclick="window.print()">⇩ Download Report</button>
        </div>
    </div>

    <div class="main-grid">
        <section class="card hero-card">
            <div class="hero-content">
                <div class="target-ring">✓</div>
                <div>
                    <div class="eyebrow">Top recommendation</div>
                    <h2>Increase price by <span>{{ result.recommended_range }}</span></h2>
                    <p>This balanced range is selected because it improves profit while keeping demand loss and downside risk within acceptable levels for this business.</p>
                </div>
            </div>
            <div class="hero-metrics">
                <div class="hero-mini">
                    <div class="label">Recommended single increase</div>
                    <div class="value">{{ result.recommended_increase }}</div>
                    <div class="sub">best point inside range</div>
                </div>
                <div class="hero-mini">
                    <div class="label">Profit improvement</div>
                    <div class="value">{{ result.profit_improvement }}</div>
                    <div class="sub">vs. current expected profit</div>
                </div>
                <div class="hero-mini">
                    <div class="label">Average demand loss</div>
                    <div class="value">{{ result.recommended_demand_loss }}</div>
                    <div class="sub">at recommended range</div>
                </div>
            </div>
        </section>

        <aside class="card recommendation-card">
            <div class="rec-head">
                <div class="rec-icon">★</div>
                <div>
                    <div class="eyebrow">Recommended range</div>
                    <h2>{{ result.recommended_range }} <span>increase</span></h2>
                    <p>Designed to balance expected profit and risk.</p>
                </div>
            </div>
            <div class="rec-separator"></div>
            <div class="rec-stats">
                <div class="rec-stat">
                    <div class="label">Expected profit</div>
                    <div class="big">{{ result.recommended_profit }} VND</div>
                    <div class="small">{{ result.profit_improvement }} vs. current</div>
                </div>
                <div class="rec-stat">
                    <div class="label">Probability of lower profit</div>
                    <div class="big">{{ result.recommended_loss_probability }}</div>
                    <div class="small">at recommended scenario</div>
                </div>
            </div>
            <div class="confidence-strip">● Balanced recommendation based on profit, demand, and downside risk</div>
        </aside>
    </div>

    <div class="section-title">
        <h2>Key Performance Indicators</h2>
        <div class="hint">All values use VND and monthly order assumptions</div>
    </div>

    <section class="kpi-grid">
        <div class="card kpi-card"><div class="kpi-icon">◇</div><div><div class="kpi-label">Current base price</div><div class="kpi-value">{{ result.base_price }}</div><div class="kpi-sub">VND/order</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">◍</div><div><div class="kpi-label">Current expected profit</div><div class="kpi-value">{{ result.current_profit }}</div><div class="kpi-sub">VND/month</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">◎</div><div><div class="kpi-label">Recommended range</div><div class="kpi-value">{{ result.recommended_range }}</div><div class="kpi-sub">increase</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">↗</div><div><div class="kpi-label">Expected profit</div><div class="kpi-value">{{ result.recommended_profit }}</div><div class="kpi-sub">VND/month</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">➜</div><div><div class="kpi-label">Best single increase</div><div class="kpi-value">{{ result.recommended_increase }}</div><div class="kpi-sub">price increase</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">↑</div><div><div class="kpi-label">Profit improvement</div><div class="kpi-value">{{ result.profit_improvement }}</div><div class="kpi-sub">vs. current</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">🛡</div><div><div class="kpi-label">Probability of lower profit</div><div class="kpi-value">{{ result.recommended_loss_probability }}</div><div class="kpi-sub">downside risk</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">👥</div><div><div class="kpi-label">Average demand</div><div class="kpi-value">{{ result.recommended_average_demand }}</div><div class="kpi-sub">orders/month</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">↘</div><div><div class="kpi-label">Average demand loss</div><div class="kpi-value">{{ result.recommended_demand_loss }}</div><div class="kpi-sub">at recommended range</div></div></div>
        <div class="card kpi-card"><div class="kpi-icon">▣</div><div><div class="kpi-label">Simulations</div><div class="kpi-value">{{ result.n_simulations }}</div><div class="kpi-sub">per price level</div></div></div>
    </section>

    <div class="section-title">
        <h2>Analytics Overview</h2>
        <div class="hint">Profit distribution is clickable and can display every tested price increase</div>
    </div>

    <section class="analytics-grid">
        <div class="card chart-card">
            <div class="chart-head"><div><h3>Profit vs. Price Increase</h3><p>Average expected profit at each tested price level</p></div></div>
            <div class="chart-wrap">{{ profit_chart | safe }}</div>
        </div>
        <div class="card chart-card distribution-launch" onclick="openDistributionModal()">
            <div>
                <div class="chart-head"><div><h3>Monte Carlo Profit Distribution</h3><p>Click to choose any tested price increase and inspect its distribution</p></div></div>
                <div class="distribution-visual" aria-hidden="true">
                    <div class="bar-demo" style="height:22%"></div><div class="bar-demo" style="height:38%"></div><div class="bar-demo" style="height:54%"></div><div class="bar-demo" style="height:78%"></div><div class="bar-demo" style="height:100%"></div><div class="bar-demo" style="height:82%"></div><div class="bar-demo" style="height:62%"></div><div class="bar-demo" style="height:44%"></div><div class="bar-demo" style="height:30%"></div>
                </div>
            </div>
            <div>
                <div class="rec-stats">
                    <div class="rec-stat"><div class="label">Default view</div><div class="big">{{ result.recommended_increase }}</div><div class="small">recommended point</div></div>
                    <div class="rec-stat"><div class="label">Risk at recommendation</div><div class="big">{{ result.recommended_loss_probability }}</div><div class="small">lower profit probability</div></div>
                </div>
                <div class="open-badge">Open Monte Carlo Distribution →</div>
            </div>
        </div>
    </section>

    <section class="analytics-grid" style="margin-top:16px; grid-template-columns: 1fr 1fr;">
        <div class="card chart-card">
            <div class="chart-head"><div><h3>Demand vs. Price Increase</h3><p>Expected monthly orders after elasticity and market pressure</p></div></div>
            <div class="chart-wrap">{{ demand_chart | safe }}</div>
        </div>
        <div class="card insights-card">
            <div class="chart-head"><div><h3>Quick Personalized Insights</h3><p>Short takeaways from this business scenario</p></div></div>
            <div class="insight-row" style="grid-template-columns: 1fr;">
                <div class="insight-item"><div class="icon">↗</div><h4>Profit opportunity</h4><p>Balanced strategy improves expected profit by {{ result.profit_improvement }} while avoiding the most aggressive range.</p></div>
                <div class="insight-item"><div class="icon">🛡</div><h4>Risk level</h4><p>There is a {{ result.recommended_loss_probability }} chance of lower profit at the recommended scenario.</p></div>
                <div class="insight-item"><div class="icon">👥</div><h4>Demand impact</h4><p>Average demand is projected at {{ result.recommended_average_demand }} orders with {{ result.recommended_demand_loss }} demand loss.</p></div>
            </div>
        </div>
    </section>

    <div class="section-title"><h2>Scenario Recommendations</h2><div class="hint">Each card keeps the original personalized advisory text</div></div>
    <section class="strategy-grid">
        <div class="card strategy-card aggressive-card">
            <div class="strategy-top"><div class="strategy-name"><div class="strategy-icon">🚀</div>Aggressive</div><span class="tag red">High upside</span></div>
            <div class="strategy-range">{{ result.aggressive_range }}</div>
            <div class="strategy-meta">
                <div class="strategy-stat"><span>Expected profit</span><strong>{{ result.aggressive_profit }} VND</strong></div>
                <div class="strategy-stat"><span>Profit improvement</span><strong>{{ result.aggressive_profit_improvement }}</strong></div>
                <div class="strategy-stat"><span>Risk</span><strong>{{ result.aggressive_risk }}</strong></div>
                <div class="strategy-stat"><span>Demand loss</span><strong>{{ result.aggressive_demand_loss }}</strong></div>
            </div>
            <div class="strategy-details">{{ result.aggressive_text | safe }}</div>
        </div>

        <div class="card strategy-card balanced-card recommended">
            <div class="strategy-top"><div class="strategy-name"><div class="strategy-icon">⚖</div>Balanced</div><span class="tag yellow">Recommended</span></div>
            <div class="strategy-range">{{ result.balanced_range }}</div>
            <div class="strategy-meta">
                <div class="strategy-stat"><span>Expected profit</span><strong>{{ result.balanced_profit }} VND</strong></div>
                <div class="strategy-stat"><span>Profit improvement</span><strong>{{ result.profit_improvement }}</strong></div>
                <div class="strategy-stat"><span>Risk</span><strong>{{ result.recommended_loss_probability }}</strong></div>
                <div class="strategy-stat"><span>Demand loss</span><strong>{{ result.recommended_demand_loss }}</strong></div>
            </div>
            <div class="strategy-details">{{ result.balanced_text | safe }}</div>
        </div>

        <div class="card strategy-card conservative-card">
            <div class="strategy-top"><div class="strategy-name"><div class="strategy-icon">🛡</div>Conservative</div><span class="tag green">Lower risk</span></div>
            <div class="strategy-range">{{ result.conservative_range }}</div>
            <div class="strategy-meta">
                <div class="strategy-stat"><span>Expected profit</span><strong>{{ result.conservative_profit }} VND</strong></div>
                <div class="strategy-stat"><span>Profit improvement</span><strong>{{ result.conservative_profit_improvement }}</strong></div>
                <div class="strategy-stat"><span>Risk</span><strong>{{ result.conservative_risk }}</strong></div>
                <div class="strategy-stat"><span>Demand loss</span><strong>{{ result.conservative_demand_loss }}</strong></div>
            </div>
            <div class="strategy-details">{{ result.conservative_text | safe }}</div>
        </div>
    </section>

    <div class="section-title"><h2>Personalized Detailed Insight</h2><div class="hint">Generated from this firm's own inputs and simulation outputs</div></div>
    <section class="card analysis-card">
        <p style="color:var(--muted-2); margin:0; line-height:1.65;">Open the full advisory explanation to see why the balanced recommendation was selected and which business factor creates the largest pressure.</p>
        <div class="analysis-actions">
            <button class="action-btn" onclick="toggleInsight()">View Full Personalized Analysis →</button>
            <a class="action-btn try-btn" href="/input">Try Again</a>
        </div>
        <div id="insightBox" class="insight-box">
            {{ result.personalized_insight | safe }}
        </div>
    </section>
</div>

<div class="modal-overlay" id="distributionModal" onclick="closeDistributionModal(event)">
    <div class="modal-window" onclick="event.stopPropagation()">
        <div class="modal-head">
            <div>
                <h2>Monte Carlo Profit Distribution by Price Increase</h2>
                <p>Select any tested price increase. The histogram updates to show the simulated profit outcomes for that exact scenario.</p>
            </div>
            <button class="close-btn" onclick="closeDistributionModal()">×</button>
        </div>
        <div class="modal-controls">
            <div class="modal-select">
                <label>Price increase</label>
                <select id="priceIncreaseSelect" onchange="renderDistributionChart()"></select>
            </div>
            <div class="modal-stat"><span>Expected profit</span><strong id="distMean">-</strong></div>
            <div class="modal-stat"><span>Lower profit probability</span><strong id="distRisk">-</strong></div>
            <div class="modal-stat"><span>Average demand</span><strong id="distDemand">-</strong></div>
        </div>
        <div id="modalDistributionChart"></div>
        <div class="modal-note">
            This distribution is generated from the Monte Carlo simulations at the selected price increase. A wider distribution means profit is more uncertain. The lower-profit probability compares each simulation outcome against current expected profit.
        </div>
    </div>
</div>

<script>
const monteCarloData = {{ monte_carlo_json | safe }};

function toggleInsight() {
    const box = document.getElementById("insightBox");
    box.style.display = box.style.display === "block" ? "none" : "block";
}

function formatVND(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
    return Number(value).toLocaleString("en-US", {maximumFractionDigits: 0}) + " VND";
}

function populateDistributionSelect() {
    const select = document.getElementById("priceIncreaseSelect");
    select.innerHTML = "";
    const keys = Object.keys(monteCarloData).sort((a,b) => Number(a) - Number(b));
    keys.forEach(k => {
        const option = document.createElement("option");
        option.value = k;
        option.textContent = Number(k).toFixed(1) + "% price increase";
        if (Number(k).toFixed(1) === "{{ result.recommended_increase_numeric }}") option.selected = true;
        select.appendChild(option);
    });
}

function renderDistributionChart() {
    const selected = document.getElementById("priceIncreaseSelect").value;
    const data = monteCarloData[selected];
    if (!data) return;

    document.getElementById("distMean").textContent = formatVND(data.mean_profit);
    document.getElementById("distRisk").textContent = data.risk_pct.toFixed(1) + "%";
    document.getElementById("distDemand").textContent = data.average_demand.toFixed(1) + " orders";

    const trace = {
        x: data.bin_centers,
        y: data.probabilities,
        type: "bar",
        marker: {
            color: data.bin_centers.map(v => v < data.current_profit ? "rgba(248,113,113,0.72)" : "rgba(38,232,137,0.78)"),
            line: {color: "rgba(255,255,255,0.12)", width: 1}
        },
        hovertemplate: "Profit: %{x:,.0f} VND<br>Probability: %{y:.2f}%<extra></extra>"
    };

    const layout = {
        title: {text: `Profit distribution at ${Number(selected).toFixed(1)}% price increase`, font: {color: "#f8fafc", size: 18}},
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: {color: "#cbd5e1"},
        margin: {l: 70, r: 30, t: 58, b: 65},
        xaxis: {title: "Simulated profit (VND)", gridcolor: "rgba(148,163,184,0.12)", zerolinecolor: "rgba(148,163,184,0.18)"},
        yaxis: {title: "Probability (%)", gridcolor: "rgba(148,163,184,0.12)"},
        shapes: [
            {type: "line", x0: data.current_profit, x1: data.current_profit, y0: 0, y1: Math.max(...data.probabilities), line: {color: "#fbbf24", width: 2, dash: "dot"}}
        ],
        annotations: [
            {x: data.current_profit, y: Math.max(...data.probabilities), text: "Current profit", showarrow: true, arrowhead: 2, ax: 40, ay: -35, font: {color: "#fbbf24"}}
        ]
    };

    Plotly.newPlot("modalDistributionChart", [trace], layout, {displayModeBar: false, responsive: true});
}

function openDistributionModal() {
    const modal = document.getElementById("distributionModal");
    modal.style.display = "flex";
    populateDistributionSelect();
    renderDistributionChart();
}

function closeDistributionModal(event) {
    if (event && event.target.id !== "distributionModal") return;
    document.getElementById("distributionModal").style.display = "none";
}

window.addEventListener("keydown", function(e) {
    if (e.key === "Escape") document.getElementById("distributionModal").style.display = "none";
});
</script>
</body>
</html>
"""


@app.route("/")
def intro():
    return render_template_string(INTRO_HTML)


@app.route("/input")
def input_page():
    return render_template_string(INPUT_HTML)


@app.route("/run", methods=["POST"])
def run_simulation():
    session["form"] = dict(request.form)
    return redirect(url_for("loading"))


@app.route("/loading")
def loading():
    return render_template_string(LOADING_HTML)


def parse_number(value):
    return float(str(value).replace(",", ""))


def swap_if_needed(a, b):
    if a > b:
        return b, a
    return a, b


def format_range_label(left, right):
    return f"{left:.0f}%–{right:.0f}%"

def format_vnd(value):
    return f"{value:,.0f} VND"


def classify_profit_improvement(value):
    if value < 0:
        return "negative"
    if value < 5:
        return "small"
    if value < 15:
        return "meaningful"
    return "strong"


def classify_demand_loss(value):
    if value < 5:
        return "low"
    if value < 15:
        return "moderate"
    if value < 25:
        return "significant"
    return "high"


def classify_risk(value):
    if value < 15:
        return "low"
    if value < 35:
        return "acceptable"
    if value < 50:
        return "elevated"
    return "high"


def classify_elasticity(value):
    if value < 1:
        return "low"
    if value < 1.5:
        return "moderate"
    if value < 2:
        return "high"
    return "very high"


def classify_fixed_cost_share(value):
    if value < 20:
        return "low"
    if value < 40:
        return "moderate"
    return "high"


def build_strategy_text(strategy_name, price_range, selected_inc, expected_profit, profit_improvement_pct,
                        demand_loss_pct, risk_pct, average_demand, elasticity, fixed_cost_share_pct):
    profit_level = classify_profit_improvement(profit_improvement_pct)
    demand_level = classify_demand_loss(demand_loss_pct)
    risk_level = classify_risk(risk_pct)
    elasticity_level = classify_elasticity(elasticity)
    fixed_cost_level = classify_fixed_cost_share(fixed_cost_share_pct)

    metrics_html = f"""
    <div class='strategy-metrics'>
        <div><b>Selected increase:</b> {selected_inc:.1f}%</div>
        <div><b>Expected profit:</b> {format_vnd(expected_profit)}</div>
        <div><b>Profit change:</b> {profit_improvement_pct:.1f}%</div>
        <div><b>Average demand:</b> {average_demand:.1f} orders</div>
        <div><b>Demand loss:</b> {demand_loss_pct:.1f}%</div>
        <div><b>Downside risk:</b> {risk_pct:.1f}%</div>
    </div>
    """

    paragraphs = []

    if strategy_name == "aggressive":
        paragraphs.append(
            f"This range is classified as <b>Aggressive</b> because it delivers the strongest expected profit among the tested price ranges. For this business, it points to a price increase around <b>{selected_inc:.1f}%</b>, with an expected profit of <b>{format_vnd(expected_profit)}</b>."
        )

        if demand_level in ["significant", "high"]:
            paragraphs.append(
                f"However, the aggressive option also creates <b>{demand_level} demand loss</b> of about <b>{demand_loss_pct:.1f}%</b>. This means the firm may lose a noticeable number of orders if customers react strongly to the price increase."
            )
        else:
            paragraphs.append(
                f"Demand loss remains <b>{demand_level}</b> at about <b>{demand_loss_pct:.1f}%</b>, so the aggressive option may be considered if the firm is confident about customer retention."
            )

        if risk_level in ["elevated", "high"]:
            paragraphs.append(
                f"The downside risk is <b>{risk_level}</b> at <b>{risk_pct:.1f}%</b>. This strategy should only be used if the firm has loyal customers, differentiated production quality, or enough bargaining power to defend a higher price."
            )
        else:
            paragraphs.append(
                f"The downside risk is <b>{risk_level}</b>. This makes the aggressive option less dangerous, but it still requires careful monitoring because it relies on customers accepting a higher price."
            )

    elif strategy_name == "balanced":
        paragraphs.append(
            f"This range is the <b>main recommendation</b> because it improves profit while keeping demand loss and downside risk within acceptable limits. For this business, the selected increase is around <b>{selected_inc:.1f}%</b>."
        )

        if profit_level == "strong":
            paragraphs.append(
                f"The expected profit improvement is <b>strong</b> at <b>{profit_improvement_pct:.1f}%</b>, meaning the firm has meaningful upside without needing to move directly to the highest-risk price range."
            )
        elif profit_level == "meaningful":
            paragraphs.append(
                f"The expected profit improvement is <b>meaningful</b> at <b>{profit_improvement_pct:.1f}%</b>. This suggests the price change can improve profitability while still remaining moderate."
            )
        elif profit_level == "small":
            paragraphs.append(
                f"The expected profit improvement is <b>small</b> at <b>{profit_improvement_pct:.1f}%</b>. This may still be useful as a cautious adjustment, but the firm should not expect a large financial upside."
            )
        else:
            paragraphs.append(
                f"The expected profit change is negative at <b>{profit_improvement_pct:.1f}%</b>. Under these assumptions, the firm should be careful and consider the conservative range."
            )

        if demand_level in ["low", "moderate"]:
            paragraphs.append(
                f"Average demand loss is <b>{demand_level}</b> at <b>{demand_loss_pct:.1f}%</b>, so the recommendation does not push order volume into a dangerous zone."
            )
        else:
            paragraphs.append(
                f"Average demand loss is <b>{demand_level}</b> at <b>{demand_loss_pct:.1f}%</b>. The firm should apply this range gradually or only to less price-sensitive customers first."
            )

        if risk_level in ["low", "acceptable"]:
            paragraphs.append(
                f"The probability of earning less than the current profit is <b>{risk_pct:.1f}%</b>, which is <b>{risk_level}</b> for a balanced pricing decision."
            )
        else:
            paragraphs.append(
                f"The probability of lower profit is <b>{risk_pct:.1f}%</b>, which is <b>{risk_level}</b>. This recommendation should be treated as a controlled test rather than an automatic price change."
            )

    else:
        paragraphs.append(
            f"This range is classified as <b>Conservative</b> because it prioritizes demand stability and lower downside risk. For this business, it points to a price increase around <b>{selected_inc:.1f}%</b>."
        )

        if elasticity_level in ["high", "very high"]:
            paragraphs.append(
                f"Historical elasticity is <b>{elasticity:.2f}</b>, which means customers are price-sensitive. This makes the conservative option safer if the firm is unsure about customer reaction."
            )
        else:
            paragraphs.append(
                f"Historical elasticity is <b>{elasticity:.2f}</b>, so customers are not extremely sensitive to price. The conservative option is still useful if the firm wants to protect relationships and order volume."
            )

        if fixed_cost_level == "high":
            paragraphs.append(
                f"Fixed cost pressure is high at <b>{fixed_cost_share_pct:.1f}%</b>. Protecting demand is important because fewer orders would spread fixed costs across a smaller volume."
            )
        else:
            paragraphs.append(
                f"Fixed cost pressure is <b>{fixed_cost_level}</b> at <b>{fixed_cost_share_pct:.1f}%</b>. This option helps reduce the risk of demand falling too much."
            )

        paragraphs.append(
            f"The expected profit change is <b>{profit_improvement_pct:.1f}%</b>, demand loss is about <b>{demand_loss_pct:.1f}%</b>, and downside risk is <b>{risk_pct:.1f}%</b>. This is suitable for a risk-averse firm or for a first-stage price test."
        )

    return metrics_html + "<br>".join(f"<p>{p}</p>" for p in paragraphs)


def build_personalized_insight(recommended_range, recommended_inc, current_profit, recommended_profit,
                               profit_improvement_pct, base_demand, recommended_average_demand,
                               recommended_demand_loss_pct, recommended_risk_pct, elasticity,
                               fixed_cost_share_pct, variable_cost_share_pct, avg_market_growth_pct,
                               avg_budget_pressure_pct, avg_material_shock_pct, avg_material_inflation_pct,
                               current_cost_per_order, base_price, material, margin_pct):
    # Create a structured, personalized advisory report for the result page.
    # The output is rule-based, but each section changes based on the firm's own simulation results.
    profit_level = classify_profit_improvement(profit_improvement_pct)
    demand_level = classify_demand_loss(recommended_demand_loss_pct)
    risk_level = classify_risk(recommended_risk_pct)
    elasticity_level = classify_elasticity(elasticity)
    fixed_cost_level = classify_fixed_cost_share(fixed_cost_share_pct)

    price_effect_pct = elasticity * recommended_inc
    net_market_effect_pct = avg_market_growth_pct - avg_budget_pressure_pct - avg_material_shock_pct

    demand_drivers = {
        "price increase effect": price_effect_pct,
        "customer budget pressure": avg_budget_pressure_pct,
        "material shock impact": avg_material_shock_pct
    }
    main_driver = max(demand_drivers, key=demand_drivers.get)
    main_driver_value = demand_drivers[main_driver]

    if profit_level == "negative":
        profit_status = "not financially attractive yet"
        profit_explain = "The recommended point does not beat the current profit baseline. The firm should not treat this as a direct price-increase signal; it should review cost structure or use a lower-risk price test first."
    elif profit_level == "small":
        profit_status = "limited profit upside"
        profit_explain = "The recommendation improves profit only slightly. It can still work as a cautious adjustment, but the firm should not expect a major financial improvement from price alone."
    elif profit_level == "meaningful":
        profit_status = "meaningful profit upside"
        profit_explain = "The recommendation creates a meaningful profit improvement without moving directly to the most aggressive price range. This is usually a good fit for a balanced pricing decision."
    else:
        profit_status = "strong profit upside"
        profit_explain = "The recommendation creates strong financial upside. The firm should still check demand loss and risk carefully because high profit improvement can sometimes come from a price increase that customers may resist."

    if demand_level == "low":
        demand_status = "stable demand"
        demand_explain = "The expected order loss is small, so the firm can raise price while keeping monthly volume relatively stable."
    elif demand_level == "moderate":
        demand_status = "manageable demand pressure"
        demand_explain = "The firm may lose some orders, but the demand impact is still manageable under the simulated market assumptions."
    elif demand_level == "significant":
        demand_status = "visible demand pressure"
        demand_explain = "The order loss is large enough to require a phased rollout. The firm should avoid applying the increase to all customers at once."
    else:
        demand_status = "high demand pressure"
        demand_explain = "The expected order loss is high. The recommended increase may be too aggressive unless the firm has strong customer loyalty, specialized quality, or weak competition."

    if risk_level == "low":
        risk_status = "low downside risk"
        risk_explain = "Only a small share of Monte Carlo simulations produces profit below the current baseline. This makes the recommendation relatively safe."
    elif risk_level == "acceptable":
        risk_status = "acceptable downside risk"
        risk_explain = "The lower-profit probability is acceptable for a balanced strategy. Most simulations still perform at or above the current profit baseline."
    elif risk_level == "elevated":
        risk_status = "elevated downside risk"
        risk_explain = "The downside risk is high enough that the firm should test this recommendation with selected customers before applying it broadly."
    else:
        risk_status = "high downside risk"
        risk_explain = "The lower-profit probability is high. A risk-averse firm should move to the conservative option or rerun the model with updated assumptions."

    if elasticity_level == "low":
        elasticity_explain = "Historical elasticity is low, so customers have not reduced demand strongly after past price changes. This gives the firm more pricing power."
    elif elasticity_level == "moderate":
        elasticity_explain = "Historical elasticity is moderate. Customers react to price, but not extremely. The firm can adjust price, but should still monitor order conversion."
    elif elasticity_level == "high":
        elasticity_explain = "Historical elasticity is high. Customers are price-sensitive, so large jumps above the balanced range can quickly reduce orders."
    else:
        elasticity_explain = "Historical elasticity is very high. Demand may fall sharply after price increases, so aggressive pricing should be avoided unless the firm has strong customer lock-in."

    if fixed_cost_level == "low":
        fixed_cost_explain = "Fixed cost pressure is low, so demand loss has a smaller effect on cost per order. The main concern is customer response, not fixed-cost absorption."
    elif fixed_cost_level == "moderate":
        fixed_cost_explain = "Fixed cost pressure is moderate. If orders fall, fixed cost per order increases, but the impact is still manageable at the recommended range."
    else:
        fixed_cost_explain = "Fixed cost pressure is high. Losing orders is dangerous because the same fixed cost must be allocated across fewer orders, increasing cost per order."

    if main_driver == "price increase effect":
        driver_action = "keep the increase inside the balanced range, avoid sudden jumps, and communicate the reason for the price change clearly."
    elif main_driver == "customer budget pressure":
        driver_action = "segment customers by budget sensitivity, offer flexible payment terms, or apply smaller increases to highly price-sensitive customers."
    else:
        driver_action = "monitor raw-material quotations, update cost assumptions regularly, and explain material-driven price changes transparently to customers."

    actions = []
    if profit_level in ["meaningful", "strong"] and risk_level in ["low", "acceptable"] and demand_level in ["low", "moderate"]:
        actions.append("Use the balanced range as the first implementation target because it improves profit while keeping demand and risk manageable.")
    if demand_level in ["significant", "high"] or risk_level in ["elevated", "high"]:
        actions.append("Roll out the increase gradually instead of applying it to all customers immediately.")
    if elasticity_level in ["high", "very high"]:
        actions.append("Avoid moving directly to the aggressive range because historical data shows customers are price-sensitive.")
    if fixed_cost_level == "high":
        actions.append("Protect order volume carefully because demand loss can raise fixed cost per order.")
    if avg_material_inflation_pct >= 8:
        actions.append("Review supplier quotations or purchasing contracts because material inflation is creating noticeable cost pressure.")
    if not actions:
        actions.append("Monitor customer response for one to two months and rerun the simulation if market assumptions change.")

    action_html = "".join(f"<li>{a}</li>" for a in actions)

    return f"""
    <div class="personalized-block advisory-summary">
        <h3>1. Executive recommendation for this business</h3>
        <p>
            The system recommends the <b>{recommended_range}</b> balanced price range, with the best point at
            <b>{recommended_inc:.1f}%</b>. At this level, expected profit moves from
            <b>{format_vnd(current_profit)}</b> to <b>{format_vnd(recommended_profit)}</b>, which is a
            <b>{profit_improvement_pct:.1f}%</b> profit change.
        </p>
        <p>
            The recommendation is classified as <b>{profit_status}</b>, with <b>{demand_status}</b> and
            <b>{risk_status}</b>. Average demand is projected at <b>{recommended_average_demand:.1f}</b> orders
            compared with the current baseline of <b>{base_demand:.1f}</b> orders.
        </p>
    </div>

    <div class="personalized-block">
        <h3>2. Decision scorecard</h3>
        <div class="insight-score-grid">
            <div><span>Profit impact</span><b>{profit_improvement_pct:.1f}%</b><small>{profit_status}</small></div>
            <div><span>Demand loss</span><b>{recommended_demand_loss_pct:.1f}%</b><small>{demand_status}</small></div>
            <div><span>Downside risk</span><b>{recommended_risk_pct:.1f}%</b><small>{risk_status}</small></div>
            <div><span>Elasticity</span><b>{elasticity:.2f}</b><small>{elasticity_level} sensitivity</small></div>
            <div><span>Fixed cost share</span><b>{fixed_cost_share_pct:.1f}%</b><small>{fixed_cost_level} pressure</small></div>
            <div><span>Material inflation</span><b>{avg_material_inflation_pct:.1f}%</b><small>average simulation</small></div>
        </div>
    </div>

    <div class="personalized-block">
        <h3>3. Why this recommendation was selected</h3>
        <p>{profit_explain}</p>
        <p>{demand_explain}</p>
        <p>{risk_explain}</p>
        <p>
            In short, the balanced range is selected because it does not only chase the highest profit.
            It also checks whether the firm can keep enough demand and avoid excessive downside risk.
        </p>
    </div>

    <div class="personalized-block">
        <h3>4. Main pressure driver behind demand change</h3>
        <p>
            The largest negative demand driver is <b>{main_driver}</b>, contributing about
            <b>{main_driver_value:.1f}%</b> demand pressure. For comparison, average market growth is
            <b>{avg_market_growth_pct:.1f}%</b>, average budget pressure is <b>{avg_budget_pressure_pct:.1f}%</b>,
            and average material shock impact is <b>{avg_material_shock_pct:.1f}%</b>.
        </p>
        <p>
            The net market effect before price elasticity is approximately <b>{net_market_effect_pct:.1f}%</b>.
            This means the pricing decision is being evaluated under a market condition that is not purely driven by price;
            customer budget and material uncertainty also affect demand.
        </p>
        <p><b>Managerial implication:</b> the firm should {driver_action}</p>
    </div>

    <div class="personalized-block">
        <h3>5. Customer sensitivity and cost structure diagnosis</h3>
        <p>{elasticity_explain}</p>
        <p>
            Current base price is <b>{format_vnd(base_price)}</b>, calculated from current cost per order of
            <b>{format_vnd(current_cost_per_order)}</b> and target margin of <b>{margin_pct:.1f}%</b>.
            Variable cost share is <b>{variable_cost_share_pct:.1f}%</b>, while fixed cost share is
            <b>{fixed_cost_share_pct:.1f}%</b>.
        </p>
        <p>{fixed_cost_explain}</p>
    </div>

    <div class="personalized-block">
        <h3>6. Implementation plan</h3>
        <ul>{action_html}</ul>
        <p>
            After implementation, the firm should compare actual orders and quotation acceptance against the simulated demand.
            If actual demand loss is higher than expected, the firm should move back toward the conservative range.
            If demand remains stable, the firm can consider testing the upper part of the balanced range.
        </p>
    </div>
    """


@app.route("/result")
def result_page():
    form = session.get("form")

    if not form:
        return redirect(url_for("input_page"))

    material = form["material"]

    tons = float(form["tons"])
    waste_rate = float(form["waste_rate"]) / 100

    workers = float(form["workers"])
    salary = parse_number(form["salary"])

    electricity_year = parse_number(form["electricity_year"])
    maintenance_year = parse_number(form["maintenance_year"])
    machine_value = parse_number(form["machine_value"])
    machine_life = float(form["machine_life"])

    base_demand = float(form["base_demand"])
    margin = float(form["margin"]) / 100

    old_price = parse_number(form["old_price"])
    new_price_history = parse_number(form["new_price_history"])
    old_demand = float(form["old_demand"])
    new_demand_history = float(form["new_demand_history"])

    price_change_pct = (new_price_history - old_price) / max(old_price, 1)
    demand_change_pct = (new_demand_history - old_demand) / max(old_demand, 1)

    if abs(price_change_pct) < 0.0001:
        elasticity = 1.0
    else:
        elasticity = abs(demand_change_pct) / abs(price_change_pct)

    elasticity = max(min(elasticity, 3.0), 0.1)

    market_growth_min = float(form["market_growth_min"]) / 100
    market_growth_max = float(form["market_growth_max"]) / 100

    budget_pressure_min = float(form["budget_pressure_min"]) / 100
    budget_pressure_max = float(form["budget_pressure_max"]) / 100

    material_shock_min = float(form["material_shock_min"]) / 100
    material_shock_max = float(form["material_shock_max"]) / 100

    material_inflation_min = float(form["material_inflation_min"]) / 100
    material_inflation_max = float(form["material_inflation_max"]) / 100

    max_price_increase = float(form["max_price_increase"])
    n_simulations = int(form["n_simulations"])

    market_growth_min, market_growth_max = swap_if_needed(market_growth_min, market_growth_max)
    budget_pressure_min, budget_pressure_max = swap_if_needed(budget_pressure_min, budget_pressure_max)
    material_shock_min, material_shock_max = swap_if_needed(material_shock_min, material_shock_max)
    material_inflation_min, material_inflation_max = swap_if_needed(material_inflation_min, material_inflation_max)

    safe_base_demand = max(base_demand, 1)

    material_unit_cost = MATERIAL_PRICE[material]

    monthly_material_cost = material_unit_cost * tons
    adjusted_material_cost = monthly_material_cost * (1 + waste_rate)

    monthly_labor_cost = workers * salary

    monthly_electricity_rent = electricity_year / 12
    monthly_maintenance = maintenance_year / 12
    monthly_depreciation = machine_value / (machine_life * 12)

    fixed_cost = monthly_electricity_rent + monthly_maintenance + monthly_depreciation
    total_monthly_cost = adjusted_material_cost + monthly_labor_cost + fixed_cost

    variable_cost_per_order = (adjusted_material_cost + monthly_labor_cost) / safe_base_demand
    fixed_cost_per_order = fixed_cost / safe_base_demand
    current_cost_per_order = variable_cost_per_order + fixed_cost_per_order

    base_price = current_cost_per_order / max(1 - margin, 0.01)
    current_profit = (base_price - current_cost_per_order) * safe_base_demand

    rows = []
    simulation_rows = []

    price_grid = np.arange(0, max_price_increase + 0.001, 0.5)

    for inc in price_grid:
        inc_rate = inc / 100

        profits = []
        demands = []
        demand_changes = []
        costs = []

        for sim in range(n_simulations):
            market_growth_sim = np.random.uniform(market_growth_min, market_growth_max)
            budget_pressure_sim = np.random.uniform(budget_pressure_min, budget_pressure_max)
            material_shock_sim = np.random.uniform(material_shock_min, material_shock_max)
            material_inflation_sim = np.random.uniform(material_inflation_min, material_inflation_max)

            total_demand_change = (
                market_growth_sim
                - budget_pressure_sim
                - material_shock_sim
                - elasticity * inc_rate
            )

            new_demand = base_demand * (1 + total_demand_change)
            new_demand = max(new_demand, 0.1)

            new_selling_price = base_price * (1 + inc_rate)

            new_variable_cost_per_order = variable_cost_per_order * (1 + material_inflation_sim)
            new_fixed_cost_per_order = fixed_cost / max(new_demand, 1)
            new_cost_per_order = new_variable_cost_per_order + new_fixed_cost_per_order

            expected_profit = (new_selling_price - new_cost_per_order) * new_demand

            profits.append(expected_profit)
            demands.append(new_demand)
            demand_changes.append(total_demand_change)
            costs.append(new_cost_per_order)

            simulation_rows.append({
                "Increase %": inc,
                "Simulation": sim + 1,
                "Elasticity": elasticity,
                "Market Growth %": market_growth_sim * 100,
                "Budget Pressure %": budget_pressure_sim * 100,
                "Material Shock Impact %": material_shock_sim * 100,
                "Material Inflation %": material_inflation_sim * 100,
                "Demand Change %": total_demand_change * 100,
                "Demand": new_demand,
                "New Cost per Order": new_cost_per_order,
                "Profit": expected_profit
            })

        profits_array = np.array(profits)
        demands_array = np.array(demands)
        demand_changes_array = np.array(demand_changes)
        costs_array = np.array(costs)

        rows.append({
            "Increase %": inc,
            "Expected Profit": profits_array.mean(),
            "Min Profit": profits_array.min(),
            "Max Profit": profits_array.max(),
            "Probability of Lower Profit": np.mean(profits_array < current_profit),
            "Average Demand": demands_array.mean(),
            "Average Demand Change %": demand_changes_array.mean() * 100,
            "Average Demand Loss %": max((base_demand - demands_array.mean()) / max(base_demand, 1) * 100, 0),
            "Average Cost per Order": costs_array.mean()
        })

    df = pd.DataFrame(rows)
    simulation_df = pd.DataFrame(simulation_rows)

    best = df.loc[df["Expected Profit"].idxmax()]
    best_inc = float(best["Increase %"])

    bin_edges = np.arange(0, max_price_increase + 2.001, 2)
    if bin_edges[-1] < max_price_increase:
        bin_edges = np.append(bin_edges, max_price_increase)

    labels = []
    for i in range(len(bin_edges) - 1):
        labels.append(format_range_label(bin_edges[i], bin_edges[i + 1]))

    df["Price Range"] = pd.cut(
        df["Increase %"],
        bins=bin_edges,
        labels=labels,
        include_lowest=True,
        right=True
    )

    range_summary = df.groupby("Price Range", observed=False).agg({
        "Expected Profit": "mean",
        "Probability of Lower Profit": "mean",
        "Average Demand": "mean",
        "Average Demand Loss %": "mean"
    }).reset_index()

    aggressive_row = range_summary.loc[range_summary["Expected Profit"].idxmax()]
    aggressive_range = str(aggressive_row["Price Range"])

    balanced_candidates = range_summary[
        (range_summary["Average Demand"] >= base_demand * 0.75) &
        (range_summary["Probability of Lower Profit"] <= 0.35)
    ]

    if balanced_candidates.empty:
        balanced_candidates = range_summary[
            range_summary["Average Demand"] >= base_demand * 0.65
        ]

    if balanced_candidates.empty:
        balanced_candidates = range_summary

    balanced_row = balanced_candidates.loc[balanced_candidates["Expected Profit"].idxmax()]
    balanced_range = str(balanced_row["Price Range"])

    conservative_candidates = range_summary[
        (range_summary["Average Demand"] >= base_demand * 0.90) &
        (range_summary["Probability of Lower Profit"] <= 0.25)
    ]

    if conservative_candidates.empty:
        conservative_candidates = range_summary[
            range_summary["Average Demand"] >= base_demand * 0.85
        ]

    if conservative_candidates.empty:
        conservative_candidates = range_summary

    conservative_row = conservative_candidates.loc[conservative_candidates["Probability of Lower Profit"].idxmin()]
    conservative_range = str(conservative_row["Price Range"])

    balanced_points = df[df["Price Range"].astype(str) == balanced_range]

    if balanced_points.empty:
        recommended_single = best
    else:
        recommended_single = balanced_points.loc[balanced_points["Expected Profit"].idxmax()]

    recommended_inc = float(recommended_single["Increase %"])

    def get_point_for_range(range_label, mode="profit"):
        points = df[df["Price Range"].astype(str) == str(range_label)]
        if points.empty:
            return best
        if mode == "risk":
            return points.loc[points["Probability of Lower Profit"].idxmin()]
        return points.loc[points["Expected Profit"].idxmax()]

    aggressive_single = get_point_for_range(aggressive_range, mode="profit")
    balanced_single = recommended_single
    conservative_single = get_point_for_range(conservative_range, mode="risk")

    fixed_cost_share_pct = fixed_cost_per_order / max(current_cost_per_order, 1) * 100
    variable_cost_share_pct = variable_cost_per_order / max(current_cost_per_order, 1) * 100
    margin_pct = margin * 100

    aggressive_inc = float(aggressive_single["Increase %"])
    balanced_inc = float(balanced_single["Increase %"])
    conservative_inc = float(conservative_single["Increase %"])

    aggressive_profit_value = float(aggressive_single["Expected Profit"])
    balanced_profit_value = float(balanced_single["Expected Profit"])
    conservative_profit_value = float(conservative_single["Expected Profit"])

    aggressive_profit_improvement_pct = (aggressive_profit_value - current_profit) / max(current_profit, 1) * 100
    balanced_profit_improvement_pct = (balanced_profit_value - current_profit) / max(current_profit, 1) * 100
    conservative_profit_improvement_pct = (conservative_profit_value - current_profit) / max(current_profit, 1) * 100

    aggressive_demand_loss_pct = float(aggressive_single["Average Demand Loss %"])
    balanced_demand_loss_pct = float(balanced_single["Average Demand Loss %"])
    conservative_demand_loss_pct = float(conservative_single["Average Demand Loss %"])

    aggressive_risk_pct = float(aggressive_single["Probability of Lower Profit"]) * 100
    balanced_risk_pct = float(balanced_single["Probability of Lower Profit"]) * 100
    conservative_risk_pct = float(conservative_single["Probability of Lower Profit"]) * 100

    aggressive_average_demand = float(aggressive_single["Average Demand"])
    balanced_average_demand = float(balanced_single["Average Demand"])
    conservative_average_demand = float(conservative_single["Average Demand"])

    # Build charts with explicit numeric arrays and scaled units to avoid Plotly auto-scaling glitches.
    profit_x = df["Increase %"].astype(float).tolist()
    profit_y_billion = (df["Expected Profit"].astype(float) / 1_000_000_000).tolist()
    demand_y = df["Average Demand"].astype(float).tolist()

    fig_profit = go.Figure()
    fig_profit.add_trace(go.Scatter(
        x=profit_x,
        y=profit_y_billion,
        mode="lines+markers",
        name="Expected profit",
        line=dict(color="#26e889", width=3, shape="spline"),
        marker=dict(size=7, color="#26e889", line=dict(width=1, color="rgba(255,255,255,0.35)")),
        hovertemplate="Price increase: %{x:.1f}%<br>Expected profit: %{y:.3f}B VND<extra></extra>"
    ))
    fig_profit.add_vrect(
        x0=float(str(balanced_range).split("%–")[0]),
        x1=float(str(balanced_range).split("%–")[1].replace("%", "")),
        fillcolor="rgba(251,191,36,0.14)",
        line_width=0,
        annotation_text="Recommended range",
        annotation_position="top left",
        annotation_font_color="#fbbf24"
    )
    fig_profit.update_layout(
        height=310,
        margin=dict(l=58, r=22, t=28, b=52),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1", size=12),
        title=dict(text="Expected Profit by Price Increase", font=dict(size=16, color="#f8fafc"), x=0.02),
        xaxis=dict(
            title="Price increase (%)",
            gridcolor="rgba(148,163,184,0.12)",
            zerolinecolor="rgba(148,163,184,0.20)",
            range=[min(profit_x), max(profit_x)],
            fixedrange=True
        ),
        yaxis=dict(
            title="Expected profit (B VND)",
            gridcolor="rgba(148,163,184,0.12)",
            fixedrange=True,
            tickformat=",.2f"
        ),
        showlegend=False
    )
    profit_chart = pio.to_html(fig_profit, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True}, default_width="100%", default_height="310px")

    fig_demand = go.Figure()
    fig_demand.add_trace(go.Scatter(
        x=profit_x,
        y=demand_y,
        mode="lines+markers",
        name="Average demand",
        line=dict(color="#38bdf8", width=3, shape="spline"),
        marker=dict(size=7, color="#38bdf8", line=dict(width=1, color="rgba(255,255,255,0.35)")),
        hovertemplate="Price increase: %{x:.1f}%<br>Average demand: %{y:.2f} orders<extra></extra>"
    ))
    fig_demand.add_vrect(
        x0=float(str(balanced_range).split("%–")[0]),
        x1=float(str(balanced_range).split("%–")[1].replace("%", "")),
        fillcolor="rgba(251,191,36,0.14)",
        line_width=0,
        annotation_text="Recommended range",
        annotation_position="top right",
        annotation_font_color="#fbbf24"
    )
    fig_demand.update_layout(
        height=310,
        margin=dict(l=58, r=22, t=28, b=52),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1", size=12),
        title=dict(text="Average Demand by Price Increase", font=dict(size=16, color="#f8fafc"), x=0.02),
        xaxis=dict(
            title="Price increase (%)",
            gridcolor="rgba(148,163,184,0.12)",
            zerolinecolor="rgba(148,163,184,0.20)",
            range=[min(profit_x), max(profit_x)],
            fixedrange=True
        ),
        yaxis=dict(
            title="Average demand (orders)",
            gridcolor="rgba(148,163,184,0.12)",
            fixedrange=True,
            rangemode="tozero"
        ),
        showlegend=False
    )
    demand_chart = pio.to_html(fig_demand, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True}, default_width="100%", default_height="310px")

    dist_df = simulation_df[np.isclose(simulation_df["Increase %"], recommended_inc)]

    if dist_df.empty:
        avg_market_growth_pct = 0
        avg_budget_pressure_pct = 0
        avg_material_shock_pct = 0
        avg_material_inflation_pct = 0
    else:
        avg_market_growth_pct = dist_df["Market Growth %"].mean()
        avg_budget_pressure_pct = dist_df["Budget Pressure %"].mean()
        avg_material_shock_pct = dist_df["Material Shock Impact %"].mean()
        avg_material_inflation_pct = dist_df["Material Inflation %"].mean()

    monte_carlo_payload = {}
    current_profit_value_for_dist = float(current_profit)
    for inc_value, group in simulation_df.groupby("Increase %"):
        profits_for_inc = group["Profit"].to_numpy(dtype=float)
        if profits_for_inc.size == 0:
            continue
        counts, edges = np.histogram(profits_for_inc, bins=32)
        probabilities = counts / max(counts.sum(), 1) * 100
        centers = (edges[:-1] + edges[1:]) / 2
        monte_carlo_payload[f"{float(inc_value):.1f}"] = {
            "bin_centers": [float(x) for x in centers],
            "probabilities": [float(y) for y in probabilities],
            "mean_profit": float(np.mean(profits_for_inc)),
            "risk_pct": float(np.mean(profits_for_inc < current_profit_value_for_dist) * 100),
            "average_demand": float(group["Demand"].mean()),
            "current_profit": current_profit_value_for_dist
        }

    monte_carlo_json = json.dumps(monte_carlo_payload)

    aggressive_text = build_strategy_text(
        "aggressive",
        aggressive_range,
        aggressive_inc,
        aggressive_profit_value,
        aggressive_profit_improvement_pct,
        aggressive_demand_loss_pct,
        aggressive_risk_pct,
        aggressive_average_demand,
        elasticity,
        fixed_cost_share_pct
    )

    balanced_text = build_strategy_text(
        "balanced",
        balanced_range,
        balanced_inc,
        balanced_profit_value,
        balanced_profit_improvement_pct,
        balanced_demand_loss_pct,
        balanced_risk_pct,
        balanced_average_demand,
        elasticity,
        fixed_cost_share_pct
    )

    conservative_text = build_strategy_text(
        "conservative",
        conservative_range,
        conservative_inc,
        conservative_profit_value,
        conservative_profit_improvement_pct,
        conservative_demand_loss_pct,
        conservative_risk_pct,
        conservative_average_demand,
        elasticity,
        fixed_cost_share_pct
    )

    personalized_insight = build_personalized_insight(
        recommended_range=balanced_range,
        recommended_inc=recommended_inc,
        current_profit=current_profit,
        recommended_profit=balanced_profit_value,
        profit_improvement_pct=balanced_profit_improvement_pct,
        base_demand=base_demand,
        recommended_average_demand=balanced_average_demand,
        recommended_demand_loss_pct=balanced_demand_loss_pct,
        recommended_risk_pct=balanced_risk_pct,
        elasticity=elasticity,
        fixed_cost_share_pct=fixed_cost_share_pct,
        variable_cost_share_pct=variable_cost_share_pct,
        avg_market_growth_pct=avg_market_growth_pct,
        avg_budget_pressure_pct=avg_budget_pressure_pct,
        avg_material_shock_pct=avg_material_shock_pct,
        avg_material_inflation_pct=avg_material_inflation_pct,
        current_cost_per_order=current_cost_per_order,
        base_price=base_price,
        material=material,
        margin_pct=margin_pct
    )

    fig_dist = px.histogram(
        dist_df,
        x="Profit",
        nbins=40,
        title=f"Profit Distribution at Recommended {recommended_inc:.1f}% Price Increase"
    )
    fig_dist.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font_color="white"
    )
    dist_chart = pio.to_html(fig_dist, full_html=False)

    result = {
        "base_price": f"{base_price:,.0f}",
        "current_profit": f"{current_profit:,.0f}",

        "aggressive_range": aggressive_range,
        "balanced_range": balanced_range,
        "conservative_range": conservative_range,

        "recommended_range": balanced_range,
        "recommended_increase": f"{recommended_inc:.1f}%",
        "recommended_profit": f"{balanced_profit_value:,.0f}",
        "recommended_loss_probability": f"{balanced_risk_pct:.1f}%",
        "recommended_average_demand": f"{balanced_average_demand:.1f}",
        "recommended_demand_loss": f"{balanced_demand_loss_pct:.1f}%",
        "profit_improvement": f"{balanced_profit_improvement_pct:.1f}%",

        "aggressive_text": aggressive_text,
        "balanced_text": balanced_text,
        "conservative_text": conservative_text,
        "personalized_insight": personalized_insight,

        "aggressive_profit": f"{aggressive_profit_value:,.0f}",
        "aggressive_profit_improvement": f"{aggressive_profit_improvement_pct:.1f}%",
        "aggressive_risk": f"{aggressive_risk_pct:.1f}%",
        "aggressive_demand_loss": f"{aggressive_demand_loss_pct:.1f}%",

        "balanced_profit": f"{balanced_profit_value:,.0f}",
        "conservative_profit": f"{conservative_profit_value:,.0f}",
        "conservative_profit_improvement": f"{conservative_profit_improvement_pct:.1f}%",
        "conservative_risk": f"{conservative_risk_pct:.1f}%",
        "conservative_demand_loss": f"{conservative_demand_loss_pct:.1f}%",

        "recommended_increase_numeric": f"{recommended_inc:.1f}",
        "n_simulations": n_simulations
    }

    return render_template_string(
        RESULT_HTML,
        result=result,
        profit_chart=profit_chart,
        demand_chart=demand_chart,
        dist_chart=dist_chart,
        monte_carlo_json=monte_carlo_json
    )


if __name__ == "__main__":
    app.run(debug=False)
