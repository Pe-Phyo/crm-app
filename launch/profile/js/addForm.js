import {
    getMyProfile,
    updateMyProfile,
    getCapabilitiesSchema,
    getMyCapabilities,
    updateMyCapabilities,
    apiCall
} from './api.js';
import { escapeHtml, setupMultiInput } from '../../students/js/utils/helpers.js';

// The modal will be injected into the dashboard shell
let modalOverlay = null;

/**
 * Opens the profile editing modal.
 * Fetches schema and current data, builds form, attaches events.
 */
export async function openProfileForm() {
    // Fetch data
    const [profile, schema, capabilities] = await Promise.all([
        getMyProfile().catch(() => null),
        getCapabilitiesSchema().catch(() => null),
        getMyCapabilities().catch(() => ({ sections: [] }))
    ]);

    if (!profile) {
        alert('Could not load profile.');
        return;
    }

    // Build modal HTML using the schema
    const formHtml = buildFormHtml(schema, profile, capabilities);

    // Create modal overlay
    modalOverlay = document.createElement('div');
    modalOverlay.className = 'modal-overlay';
    modalOverlay.id = 'profileModal';
    modalOverlay.innerHTML = `
        <div class="modal" style="max-width:800px;max-height:90vh;overflow-y:auto;">
            <h2>Edit Your Profile</h2>
            <form id="profileEditForm">
                ${formHtml}
                <div class="modal-actions" style="margin-top:20px;">
                    <button type="button" class="btn btn-secondary" id="profileModalCancel">Cancel</button>
                    <button type="submit" class="btn btn-success">Save Profile</button>
                </div>
            </form>
        </div>
    `;

    document.body.appendChild(modalOverlay);

    // Cancel handler
    document.getElementById('profileModalCancel').addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
    });

    // Set up multi‑input fields (phones, emails, etc.) — we know they're in the schema
    setupMultiInput('profilePhonesContainer', 'profile-phone-input');
    setupMultiInput('profileEmailsContainer', 'profile-email-input');
    // Additional multi‑inputs can be set up similarly based on schema

    // Submit handler
    document.getElementById('profileEditForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleSubmit(profile, schema);
    });
}

/**
 * Builds the inner HTML of the form from the schema definition.
 */
function buildFormHtml(schema, profile, capabilities) {
    if (!schema || !schema.sections) {
        return '<p>Form configuration not available.</p>';
    }

    let html = '';
    schema.sections.forEach(section => {
        html += `<fieldset class="form-section">
                    <legend>${escapeHtml(section.legend)}</legend>`;

        section.fields.forEach(field => {
            const value = getFieldValue(field.name, profile, capabilities);
            html += buildFieldHtml(field, value);
        });

        html += '</fieldset>';
    });

    return html;
}

/**
 * Retrieves the current value for a field from profile or capability data.
 */
function getFieldValue(name, profile, capabilities) {
    // Identity fields are in the profile object
    if (profile && profile.hasOwnProperty(name)) {
        return profile[name];
    }
    // Capability fields are stored in sections
    if (capabilities && capabilities.sections) {
        for (const section of capabilities.sections) {
            const field = section.fields?.find(f => f.name === name);
            if (field) return field.value;
        }
    }
    return '';
}

/**
 * Generates the HTML for a single field based on its type.
 */
function buildFieldHtml(field, value) {
    let inputHtml = '';
    const val = escapeHtml(String(value || ''));

    switch (field.type) {
        case 'text':
        case 'email':
        case 'password':
            inputHtml = `<input type="${field.type}" name="${field.name}" value="${val}">`;
            break;
        case 'textarea':
            inputHtml = `<textarea name="${field.name}" rows="3">${val}</textarea>`;
            break;
        case 'select':
            const options = (field.options || []).map(opt =>
                `<option value="${opt.value}" ${val === opt.value ? 'selected' : ''}>${opt.label}</option>`
            ).join('');
            inputHtml = `<select name="${field.name}">${options}</select>`;
            break;
        case 'checkbox':
            inputHtml = `<label style="display:flex;align-items:center;">
                            <input type="checkbox" name="${field.name}" ${val === 'true' ? 'checked' : ''} style="width:auto;margin-right:0.5em;"> ${escapeHtml(field.label)}
                        </label>`;
            break;
        case 'multi-input':
            // Multi‑input container (e.g., phones, emails)
            inputHtml = `<div id="${field.containerId}" class="multi-input-container">
                            <div class="multi-input-row">
                                <input type="text" name="${field.name}[]" class="${field.inputClass}" value="${val}">
                                <button type="button" class="add-multi-btn">+</button>
                            </div>
                         </div>`;
            break;
        // Additional types can be added
        default:
            inputHtml = `<input type="text" name="${field.name}" value="${val}">`;
    }

    return `<label>${escapeHtml(field.label)}</label>${inputHtml}`;
}

/**
 * Collects form data and submits to the appropriate endpoints.
 */
async function handleSubmit(profile, schema) {
    const form = document.getElementById('profileEditForm');
    const formData = new FormData(form);

    // Separate identity fields from capability fields based on schema
    const identityData = {};
    const capabilitySections = {};

    schema.sections.forEach(section => {
        section.fields.forEach(field => {
            const value = formData.get(field.name);
            if (field.section === 'identity') {
                identityData[field.name] = value;
            } else {
                if (!capabilitySections[section.id]) {
                    capabilitySections[section.id] = { fields: [] };
                }
                capabilitySections[section.id].fields.push({
                    name: field.name,
                    value: value
                });
            }
        });
    });

    // Special handling for multi‑input fields
    identityData.phones = Array.from(form.querySelectorAll('.profile-phone-input'))
        .map(inp => inp.value.trim()).filter(v => v);
    identityData.emails = Array.from(form.querySelectorAll('.profile-email-input'))
        .map(inp => inp.value.trim()).filter(v => v);

    try {
        // Update identity
        await updateMyProfile(identityData);

        // Update capabilities (if any sections exist)
        if (Object.keys(capabilitySections).length > 0) {
            await updateMyCapabilities(capabilitySections);
        }

        alert('Profile updated successfully.');
        closeModal();
        // Optionally refresh the dashboard
        window.location.reload();
    } catch (err) {
        alert('Update failed: ' + err.message);
    }
}

function closeModal() {
    if (modalOverlay) {
        modalOverlay.remove();
        modalOverlay = null;
    }
}