import { useState } from 'react';
import { Field, Modal, Numeric } from './components';
import { type Price } from './types';

export function CustomPrice({ onClose, onSave }: { onClose: () => void; onSave: (p: Price) => void }) {
  const [values, setValues] = useState({
    name: '',
    provider: 'Custom',
    input: '',
    output: '',
    cache_read: '',
    cache_write: '',
  });
  const [error, setError] = useState('');
  return (
    <Modal title="Add custom model rates" onClose={onClose}>
      <p className="muted">
        Use a unique model ID for negotiated rates or a model missing from the catalog. All prices are USD per
        million tokens.
      </p>
      <div className="form-grid">
        <Field label="Custom model ID">
          <input
            value={values.name}
            onChange={(e) => setValues({ ...values, name: e.target.value })}
            placeholder="e.g. customer/contract-model"
          />
        </Field>
        <Field label="Provider name">
          <input
            value={values.provider}
            onChange={(e) => setValues({ ...values, provider: e.target.value })}
          />
        </Field>
        {(['input', 'output', 'cache_read', 'cache_write'] as const).map((k) => (
          <Numeric
            key={k}
            label={`${k.replaceAll('_', ' ')} USD / 1M`}
            value={values[k]}
            onChange={(v) => setValues({ ...values, [k]: v })}
            hint={k.startsWith('cache') ? 'Optional. Blank means unavailable.' : undefined}
          />
        ))}
      </div>
      <p className="muted small">
        Custom rates are uniform. Use a separate model ID for a different region, service tier, or cache
        duration.
      </p>
      {error && (
        <p className="invalid-text" role="alert">
          {error}
        </p>
      )}
      <div className="modal-actions">
        <button className="button subtle" onClick={onClose}>
          Cancel
        </button>
        <button
          className="button dark"
          onClick={() => {
            try {
              if (
                !values.name.trim() ||
                !values.provider.trim() ||
                values.input === '' ||
                values.output === '' ||
                ![values.input, values.output, values.cache_read || '0', values.cache_write || '0'].every(
                  (v) => Number.isFinite(Number(v)) && Number(v) >= 0,
                )
              )
                throw new Error('Enter a name, provider and nonnegative input/output rates.');
              onSave({
                id: values.name.trim(),
                provider: values.provider.trim(),
                input: values.input,
                output: values.output,
                cache_read: values.cache_read || null,
                cache_write: values.cache_write || null,
                max_input: null,
                max_output: null,
                tiers: [],
                source: 'Architect-supplied custom rates',
                retrieved_at: new Date().toISOString(),
                custom: true,
                unsupported: [],
              });
            } catch (e) {
              setError(String(e));
            }
          }}
        >
          Add model
        </button>
      </div>
    </Modal>
  );
}
