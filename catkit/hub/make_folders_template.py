#!/usr/bin/python
from .tools import check_reaction
import os
import json

username = os.environ['USER']


# ---------publication info------------
def main(
        title,
        authors,
        year,
        journal='',
        volume='',
        number='',
        pages='',
        publisher='',
        doi='',
        tags=[],
        DFT_code='Quantum ESPRESSO',
        DFT_functional='BEEF-vdW',
        reactions=[
            {'reactants': ['2.0H2Ogas', '-1.5H2gas', 'star'],
             'products': ['OOHstar@ontop']}],
        energy_corrections={},
        bulk_compositions=['Pt', 'Ag'],
        crystal_structures=['fcc', 'hcp'],
        facets=['111'],
        custom_base=None):
    """Automatically generate an organized folder structure for a DFT
    calculation.

    Start by copying the script to a folder in your username
    and assign the right information to the arguments in the function.

    You can change the parameters and run the script several times if you,
    for example, are using different functionals or are doing different
    reactions on different surfaces.

    Remember to include the reaction that gives the adsorption energy of
    reaction intermediates, taking gas phase molecules as references
    (preferably H20, H2, CH4, CO, NH3).

    Parameters
    ----------
    title : str
        Publication or working title if not yet published.
    authors : list
        Author names, e.g. ['Doe, John', 'Einstein, Albert']
    year : str
        Year of (submission?)
    journal : str
        Publications journal name
    volume : str, optional
        Publications volume number
    number : str, optional
        Publication number
    pages : str, optional
        Publication page numbers
    publisher : str, optional
        Publisher name
    doi : str, optional
        DOI of publication
    tags : list, optional
        User defined quire tags
    DFT_code : str, optional
        e.g. 'Quantum ESPRESSO'
    DFT_functional : str, optional
        Calculator functional used, e.g. 'BEEF-vdW'
    reactions : list of dict, optional
        A new dictionary is required for each reaction, and should include two
        lists, 'reactants' and 'products'. Remember to include a minus sign and
        prefactor in the name when relevant. If your reaction is not balanced,
        you will receive an error when running the script.

        Include the phase if mixing gas phase and surface phase.
        e.g. 'star' for empty site or adsorbed phase, 'gas' if in gas phase.

        Include the adsorption site if relevant.
        e.g. star@top or star@bridge.

        For example, we can write an entry for the adsorption of CH2:
        CH4(g) - H2(g) + * -> CH2*

        as:
        {'reactants': ['CH4gas', 'H2gas', 'star'],
        'products': ['CH2star@bridge']}

        A complete entry could read:
        reactions = [
        {'reactants': ['CH4gas', '-H2gas', 'star'],
        'products': ['CH2star@bridge']},
        {'reactants': ['CH4gas', '-0.5H2gas', 'star'],
        'products': ['CH3star@top']}]

    energy_corrections : dict, optional
        e.g. {'H2gas': 0.1}
    bulk_compositions  : list of str, optional
        e.g. ['Pt', 'Ag']
    crystal_structures : list of str, optional
        e.g. ['fcc', 'hcp']
    facets : list, optional
        For complicated structures use term you would use in publication.
        e.g. ['111']
    custom_base : str, optional
        TODO
    """
    for reaction in reactions:
        check_reaction(reaction['reactants'], reaction['products'])

    # Set up directories
    if custom_base is not None:
        base = custom_base + '/'
    else:
        catbase = os.path.abspath(os.path.curdir)
        base = '%s/%s/' % (catbase, username)

    if not os.path.exists(base):
        os.mkdir(base)

    publication_shortname = '%s_%s_%s' % (authors[0].split(',')[0].lower(),
                                          title.split()[0].lower(), year)

    publication_base = base + publication_shortname + '/'

    if not os.path.exists(publication_base):
        os.mkdir(publication_base)

    # save publication info to publications.txt
    publication_dict = {'title': title,
                        'authors': authors,
                        'journal': journal,
                        'volume': volume,
                        'number': number,
                        'pages': pages,
                        'year': year,
                        'publisher': publisher,
                        'doi': doi,
                        'tags': tags
                        }

    pub_txt = publication_base + 'publication.txt'
    json.dump(publication_dict, open(pub_txt, 'w'))

    if not len(energy_corrections.keys()) == 0:
        energy_txt = publication_base + 'energy_corrections.txt'
        json.dump(energy_corrections, open(energy_txt, 'wb'))

    def create(path):
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    base = create(publication_base + DFT_code + '/')
    bulk_base = create(base + DFT_functional + '/')
    gas_base = create(bulk_base + '/gas/')

    gas_names = []
    ads_names = []
    from catkit.hub.ase_tools import get_state, clear_state, clear_prefactor
    for i in range(len(reactions)):
        rnames = [r.split('@')[0] for r in reactions[i]['reactants'] +
                  reactions[i]['products']]
        states = [get_state(r) for r in rnames]
        gas_names += [clear_state(clear_prefactor(rnames[i]))
                      for i in range(len(states)) if states[i] == 'gas']

    for name in set(gas_names):
        with open(gas_base + 'MISSING: {}_gas.traj'.format(name), 'w'):
            pass

    for bulk in bulk_compositions:
        for crystal_structure in crystal_structures:
            bulk_name = bulk + '_' + crystal_structure
            facet_base = create(bulk_base + bulk_name + '/')
            with open(facet_base + 'MISSING: {}_bulk.traj'.format(bulk_name),
                      'w'):
                pass

            for facet in facets:
                reaction_base = create(facet_base + facet + '/')
                with open(reaction_base + 'MISSING: empty_slab.traj'
                          .format(bulk_name), 'w'):
                    pass

                for i in range(len(reactions)):
                    rname = '_'.join(reactions[i]['reactants'])
                    pname = '_'.join(reactions[i]['products'])
                    reaction_name = '__'.join([rname, pname])
                    base = create(reaction_base + reaction_name + '/')
                    rnames = [r.split('@')[0] for r in
                              reactions[i]['reactants'] +
                              reactions[i]['products']]
                    states = [get_state(r) for r in rnames]

                    ads_names = [clear_prefactor(clear_state(rnames[i]))
                                 for i in range(len(states))
                                 if states[i] == 'star']

                    for ads in ads_names:
                        if ads == '':
                            continue
                        with open(base + 'MISSING: {}.traj'.format(ads), 'w'):
                            pass


if __name__ == "__main__":
    main()
