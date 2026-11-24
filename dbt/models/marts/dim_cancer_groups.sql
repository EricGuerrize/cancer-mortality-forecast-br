select
    cancer_group,
    label_pt as cancer_group_label,
    cid_start,
    cid_end
from {{ ref('cancer_group_labels') }}
