// Simple laws controller returning static law entries
const getLaws = async (req, res) => {
  try {
    const laws = [
      { id: 'constitution', title: 'Constitution of Nepal 2072', summary: 'Supreme law of Nepal.' },
      { id: 'muluki_criminal', title: 'Muluki Criminal Code', summary: 'Criminal laws and penalties.' },
      { id: 'evidence_act', title: 'Evidence Act', summary: 'Rules of evidence and admissibility.' },
      { id: 'labour_law', title: 'Muluki Labour Law', summary: 'Employment and labour rights.' },
      { id: 'company_act', title: 'Company Act 2013', summary: 'Corporate formation and governance.' }
    ];

    return res.status(200).json({ status: 'success', data: laws });
  } catch (err) {
    console.error('getLaws error:', err);
    return res.status(500).json({ status: 'error', message: 'Failed to fetch laws' });
  }
};

module.exports = { getLaws };
