// Dynamically load modal CSS when first used
if (!document.querySelector('link[href$="profile/css/styles.css"]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/launch/profile/css/styles.css';
    document.head.appendChild(link);
}

import { escapeHtml } from '../../students/js/utils/helpers.js';
import {
    updateMyProfile,
    getCapabilitiesSchema,
    getMyCapabilities,
    updateMyCapabilities
} from '../../staff/js/api.js';

export async function openProfileModal(profileData) {
    const [schema, capabilities] = await Promise.all([
        getCapabilitiesSchema().catch(() => null),
        getMyCapabilities().catch(() => ({}))
    ]);

    if (!schema || !schema.sections) {
        alert('Profile form configuration not available.');
        return;
    }

    const formHtml = buildFormHtml(schema, profileData, capabilities);

    const modalOverlay = document.createElement('div');
    modalOverlay.className = 'modal-overlay';
    modalOverlay.id = 'profileEditModal';
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
    document.getElementById('profileModalCancel').addEventListener('click', () => modalOverlay.remove());
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) modalOverlay.remove();
    });

    document.getElementById('profileEditForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleSubmit(profileData, schema);
        modalOverlay.remove();
    });
}

function buildFormHtml(schema, profileData, capabilities) {
    const CAPABILITY_KEYS = ['teaching_subjects','teaching_modes','teaching_styles','student_types','curriculum_expertise','certifications'];
    let html = '';
    schema.sections.forEach(section => {
        html += `<fieldset class="form-section"><legend>${escapeHtml(section.legend)}</legend>`;
        const isCapSection = CAPABILITY_KEYS.includes(section.id);
        if (isCapSection) {
            const capArray = (capabilities && capabilities[section.id]) || [];
            section.fields.forEach(field => {
                if (field.type === 'repeater') html += buildRepeaterField(field, section.id, { [section.id]: capArray });
                else if (field.type === 'checkboxes') html += buildCheckboxesField(field, capArray);
                else html += buildSimpleField(field, '');
            });
        } else {
            section.fields.forEach(field => {
                let value = '';
                if (profileData && profileData.hasOwnProperty(field.name)) value = profileData[field.name];
                else if (capabilities && capabilities[section.id]) {
                    const capField = capabilities[section.id].find(f => f.name === field.name);
                    if (capField) value = capField.value;
                }
                if (field.type === 'repeater') html += buildRepeaterField(field, section.id, capabilities);
                else if (field.type === 'checkboxes') html += buildCheckboxesField(field, value);
                else html += buildSimpleField(field, value);
            });
        }
        html += '</fieldset>';
    });
    return html;
}

function buildSimpleField(field, value) {
    const val = escapeHtml(String(value || ''));
    let inputHtml;
    switch (field.type) {
        case 'textarea': inputHtml = `<textarea name="${field.name}" rows="3">${val}</textarea>`; break;
        case 'select': inputHtml = `<select name="${field.name}">${(field.options||[]).map(o => `<option value="${o.value}" ${val===o.value?'selected':''}>${o.label}</option>`).join('')}</select>`; break;
        case 'number': inputHtml = `<input type="number" name="${field.name}" value="${val}" min="${field.min||0}">`; break;
        default: inputHtml = `<input type="${field.type}" name="${field.name}" value="${val}">`;
    }
    return `<label>${escapeHtml(field.label)}</label>${inputHtml}`;
}

function buildCheckboxesField(field, values) {
    const selected = Array.isArray(values) ? values : (values ? values.split(',') : []);
    const checkboxes = (field.options || []).map(opt => `
        <label style="display:inline-flex;align-items:center;margin-right:1em;">
            <input type="checkbox" name="${field.name}" value="${opt.value}" ${selected.includes(opt.value)?'checked':''} style="width:auto;margin-right:0.3em;">
            ${escapeHtml(opt.label)}
        </label>
    `).join('');
    return `<label>${escapeHtml(field.label)}</label><div style="margin-top:0.3em;">${checkboxes}</div>`;
}

function buildRepeaterField(field, sectionId, capabilities) {
    const items = (capabilities && capabilities[sectionId] && capabilities[sectionId][field.name]) || [];
    const rowsHtml = items.map((item, idx) => `
        <div class="repeater-row" data-index="${idx}">
            ${field.fields.map(sub => {
                const subVal = item[sub.name] || '';
                return buildSimpleField({...sub, name: `${sectionId}_${field.name}_${idx}_${sub.name}`}, subVal);
            }).join('')}
            <button type="button" class="remove-repeater-btn btn btn-secondary" style="margin-top:0.5em;">Remove</button>
        </div>
    `).join('');

    const templateRow = field.fields.map(sub => {
        return buildSimpleField({...sub, name: `${sectionId}_${field.name}_NEW_${sub.name}`}, '');
    }).join('') + `<button type="button" class="remove-repeater-btn btn btn-secondary" style="margin-top:0.5em;">Remove</button>`;

    return `
        <div class="repeater-container" data-section="${sectionId}" data-field="${field.name}" data-template='${escapeHtml(templateRow)}'>
            <label>${escapeHtml(field.label)}</label>
            <div class="repeater-rows">${rowsHtml}</div>
            <button type="button" class="add-repeater-btn btn btn-secondary" style="margin-top:0.5em;">+ Add</button>
        </div>
    `;
}

async function handleSubmit(profileData, schema) {
    const form = document.getElementById('profileEditForm');
    const formData = new FormData(form);
    const identityFields = ['full_name','display_name','email','phone','timezone','default_hourly_rate','bio','languages'];
    const identityData = {};
    identityFields.forEach(f => { if (formData.has(f)) identityData[f] = formData.get(f); });
    identityData.default_hourly_rate = parseInt(identityData.default_hourly_rate, 10) || 0;

    const CAPABILITY_KEYS = ['teaching_subjects','teaching_modes','teaching_styles','student_types','curriculum_expertise','certifications'];
    const capabilityData = {};

    schema.sections.forEach(section => {
        if (section.id === 'identity') return;
        const sectionKey = section.id;
        if (CAPABILITY_KEYS.includes(sectionKey)) {
            section.fields.forEach(field => {
                if (field.type === 'checkboxes') capabilityData[sectionKey] = formData.getAll(field.name);
                else if (field.type === 'repeater') {
                    const container = form.querySelector(`.repeater-container[data-section="${sectionKey}"][data-field="${field.name}"]`);
                    const items = [];
                    if (container) {
                        container.querySelectorAll('.repeater-row').forEach(row => {
                            const item = {};
                            field.fields.forEach(sub => {
                                const input = row.querySelector(`[name="${sectionKey}_${field.name}_${row.dataset.index}_${sub.name}"]`);
                                if (input) item[sub.name] = input.value;
                            });
                            items.push(item);
                        });
                    }
                    capabilityData[sectionKey] = items;
                }
            });
        }
    });

    try {
        await updateMyProfile(identityData);
        if (Object.keys(capabilityData).length > 0) await updateMyCapabilities(capabilityData);
        alert('Profile updated. Reloading...');
        window.location.reload();
    } catch (err) {
        alert('Update failed: ' + err.message);
    }
}

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('add-repeater-btn')) {
        const container = e.target.closest('.repeater-container');
        const rowsDiv = container.querySelector('.repeater-rows');
        const newIndex = rowsDiv.children.length;
        const newRow = document.createElement('div');
        newRow.className = 'repeater-row';
        newRow.dataset.index = newIndex;
        newRow.innerHTML = container.dataset.template.replace(/_NEW_/g, `_${newIndex}_`);
        rowsDiv.appendChild(newRow);
    } else if (e.target.classList.contains('remove-repeater-btn')) {
        const row = e.target.closest('.repeater-row');
        if (row) {
            const container = row.closest('.repeater-container');
            row.remove();
            if (container) {
                container.querySelectorAll('.repeater-row').forEach((r, i) => {
                    r.dataset.index = i;
                    r.querySelectorAll('[name]').forEach(input => {
                        const name = input.getAttribute('name');
                        if (name) input.setAttribute('name', name.replace(/_\d+_/, `_${i}_`));
                    });
                });
            }
        }
    }
});
