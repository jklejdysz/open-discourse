from od_lib.helper_functions.clean_text import clean
import od_lib.definitions.path_definitions as path_definitions
import xml.etree.ElementTree as et
import os
import regex
import dicttoxml

def clean(filetext, remove_pdf_header=True):
    # Replaces all the misrecognized characters
    filetext = filetext.replace(r"", "-")
    filetext = filetext.replace(r"", "-")
    filetext = filetext.replace("—", "-")
    filetext = filetext.replace("–", "-")
    filetext = filetext.replace("•", "")
    filetext = regex.sub(r"\t+", " ", filetext)
    filetext = regex.sub(r"  +", " ", filetext)

    # Remove pdf artifact
    if remove_pdf_header:
        first_part = filetext[:1000]
        rest_part = filetext[1000:]
        first_part = regex.sub(
            r"(?:Deutscher\s?Bundestag\s?-(?:\s?\d{1,2}\s?[,.]\s?Wahlperiode\s?-)?)?\s?\d{1,3}\s?[,.]\s?Sitzung\s?[,.]\s?(?:(?:Bonn|Berlin)[,.])?\s?[^,.]+,\s?den\s?\d{1,2}\s?[,.]\s?[^\d]+\d{4}.*",  # noqa: E501
            r"\n",
            first_part,
        )
        filetext = first_part + rest_part
        filetext = regex.sub(r"\s*(\(A\)|\(B\)|\(C\)|\(D\))", "", filetext)

    # Remove delimeter
    filetext = regex.sub(r"-\n+(?![^(]*\))", "", filetext)

    # Deletes all the newlines in brackets
    bracket_text = regex.finditer(r"\(([^(\)]*(\(([^(\)]*)\))*[^(\)]*)\)", filetext)

    for bracket in bracket_text:
        filetext = filetext.replace(
            str(bracket.group()),
            regex.sub(
                r"\n+",
                " ",
                regex.sub(
                    r"(^((?<!Abg\.).)+|^.*\[.+)(-\n+)",
                    r"\1",
                    str(bracket.group()),
                    flags=regex.MULTILINE,
                ),
            ),
        )
    return filetext


# input directory
RAW_XML = path_definitions.RAW_XML

# output directory
RAW_TXT = path_definitions.RAW_TXT

if not os.path.exists(RAW_TXT):
    os.makedirs(RAW_TXT)

# Open every xml plenar file in every electoral term.
for electoral_term_folder in sorted(os.listdir(RAW_XML)):
    electoral_term_folder_path = os.path.join(RAW_XML, electoral_term_folder)

    # Skip e.g. the .DS_Store file.
    if not os.path.isdir(electoral_term_folder_path):
        continue

    if electoral_term_folder not in ["electoral_term_01", "electoral_term_02"]:
        continue

    # JK: this pattern do not capture sentences like this: 02078.xml '4332\nDie Sitzung wird um 9 Uhr durch den Präsidenten\nD. Dr. Gerstenmaier eröffnet'
    begin_pattern = regex.compile(
        r"Die.*?Sitzung.*?wird.*?\d{1,2}.*?Uhr.*?(durch.*?den.*?)?(eröffnet|eingeleitet|aufgenommen)"
    )

    alternative_begin_pattern = regex.compile(
        r"Die[^\.]*?Sitzung[^\.]*?wird[^\.]*?\d{1,2}[^\.]*?Uhr[^\.]*?(durch[^\.]*?den.*?)?(eröffnet|eingeleitet|aufgenommen)[^\.]*?[.]",
        regex.V0 | regex.DOTALL
    )



   # appendix_pattern = regex.compile(r"\(Schluß.*?Sitzung.*?Uhr.*?\)")
    appendix_pattern = regex.compile(r"\((Schluß.*?Sitzung.*?Uhr.*?)|(Unterbrechung.*?Sitzung.*?Uhr.*?)\)")

    for xml_file in sorted(os.listdir(electoral_term_folder_path)):
        if ".xml" in xml_file:
            print(xml_file)
            path = os.path.join(electoral_term_folder_path, xml_file)
            tree = et.parse(path)
            meta_data = {}

            # Get the document number, the date of the session and the content.
            meta_data["document_number"] = tree.find("NR").text
            meta_data["date"] = tree.find("DATUM").text
            text_corpus = tree.find("TEXT").text

            # Clean text corpus.
            # Remove newline if it is preceded by a lower case letter. (i.e. inside the sentence)
            text_corpus = regex.sub(r'(?<=[a-z])\n', ' ', text_corpus)
            text_corpus = clean(text_corpus)
            #text_corpus
            # Find the beginnings and endings of the spoken contents in the
            # pattern plenar files.
          #  test="\nDie Sitzung wird um 17 Uhr 54 Minuten durch den Präsidenten Dr. Köhler wieder eröffnet.\nPräsident Dr."
          #  list(regex.finditer(begin_pattern, test))

            find_beginnings = list(regex.finditer(begin_pattern, text_corpus))
            find_beginnings

            if len(find_beginnings) == 0:
                print("applying different pattern beginnings")
                find_beginnings = list(regex.finditer(alternative_begin_pattern, text_corpus))

            find_endings = list(regex.finditer(appendix_pattern, text_corpus))
            find_endings

            beginning_of_session = find_beginnings[0].span()[1]

            toc = text_corpus[:beginning_of_session]
            # Append "END OF FILE" to document text, otherwise pattern is
            # not found, when appearing at the end of the file.


            text_corpus += "\n\nEND OF FILE"

            session_content = ""

            # Just extract spoken parts between the matching of the
            # beginning and the ending pattern. TOC and APPENDIX is
            # disregarded. For example: If a session is interrupted and
            # continued on the next day, there is again a whole table of content
            # section with the names of all the speakers, which should not be
            # included in the usual spoken content.
            if len(find_beginnings) == 0:
                print("no beginning found")
                continue
            elif len(find_beginnings) > len(find_endings) and len(find_endings) == 1:
                session_content = text_corpus[
                    find_beginnings[0].span()[1] : find_endings[0].span()[0]
                ]
            elif len(find_beginnings) == len(find_endings):
                for begin, end in zip(find_beginnings, find_endings):
                    session_content += text_corpus[begin.span()[1] : end.span()[0]]
            else:
                print("mismatch beginning/ending")
                print(xml_file)
                continue

            print(xml_file)


            save_path = os.path.join(
                RAW_TXT, electoral_term_folder, xml_file.replace(".xml", "")
            )

            # Save table of content, spoken content and appendix
            # in separate folders.
            if not os.path.exists(save_path):
                print(save_path)
                os.makedirs(save_path)

            if not os.path.exists(os.path.join(save_path, "session_content.txt")):
                print("saving session content")
                with open(os.path.join(save_path, "session_content.txt"), "w") as text_file:
                    text_file.write(session_content)

            if not os.path.exists(os.path.join(save_path, "meta_data.xml")):
                with open(os.path.join(save_path, "meta_data.xml"), "wb") as result_file:
                    result_file.write(dicttoxml.dicttoxml(meta_data))

            if not os.path.exists(os.path.join(save_path, "toc.txt")):
                with open(os.path.join(save_path, "toc.txt"), "w") as text_file:
                    text_file.write(toc)

