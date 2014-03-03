# -*- coding: utf-8 -*-
from utils.Regex import Regex

__author__ = 'Rabbi-Tuly'

if __name__=='__main__':
    text = '''<table style="width: 187px;" align="center" background=" border="0" cellpadding="0" cellspacing="0"> <tbody> <tr> <td colspan="2"><img src="http://img.photobucket.com/albums/v402/WGT-32/1.png" /> &nbsp;<a href="http://eshops.mercadolivre.com.br/quackstore/" target="_blank"><img src="http://img.photobucket.com/albums/v402/WGT-32/2.png" border="0" /></a> <img src="http://img.photobucket.com/albums/v402/WGT-32/3.png" /> <table style="width: 100%;" border="0" cellpadding="0" cellspacing="0"> <tbody> <tr> <td style="padding-left: 60px;" background="http://img.photobucket.com/albums/v402/WGT-32/fundo.png"> <p>&nbsp;</p> <p> Esta nova edi\xe7\xe3o, com novas quest\xf5es de concursos recentes, foi cuidadosamente composta e organizada no sentido de atender a uma necessidade espec\xedfica do mercado \x96 oferecer subs\xeddios a todos aqueles que desejam assimilar uma base conceitual para poder concorrer a concursos p\xfablicos ou enfrentar processos seletivos sofisticados que imp\xf5em a necessidade de conhecimentos b\xe1sicos sobre Administra\xe7\xe3o Geral ou Administra\xe7\xe3o P\xfablica ou ambas. Sendo tamb\xe9m de grande uso para todos os leitores que se interessam no assunto.<br/> <br /> <b>I.S.B.N.: </b>9788520432457<br/> <br/> <b>C\xf3d. Barras: </b>9788520432457<br/> <br/> <b>Reduzido: </b>4067139<br/> <br/> <b>Altura: </b>24 cm.<br/><br/><b>Largura: </b>17 cm.<br/><br/><b>Profundidade: </b>2 cm.<br/><br/><b>Acabamento : </b>Brochura<br/><br/><b>Edi\xe7\xe3o : </b>3 / 2012<br/><br/><b>Idioma : </b>Portugu\xeas<br/><br/><b>Pa\xeds de Origem : </b>Brasil<br/><br/><b>N\xfamero de Paginas : </b>536<br/><br/> <br /></p> <p>&nbsp;</p> <p style="text-align: center;"></p> </td> </tr> </tbody> </table> <img src="http://img.photobucket.com/albums/v402/WGT-32/5.png" /><br /> <img src="http://img.photobucket.com/albums/v402/WGT-32/6.png" /><br /> <img src="http://img.photobucket.com/albums/v402/WGT-32/7.png" /><br /> <img src="http://img.photobucket.com/albums/v402/WGT-32/8_usa_pf.png" /><br /> <img src="http://img.photobucket.com/albums/v402/WGT-32/10.png" /><br /> <img src="http://img.photobucket.com/albums/v402/WGT-32/11.png" /></td> </tr> <tr> <td valign="top" width="186"></td> <td valign="top" width="1"></td> </tr> <tr> <td colspan="2"></td> </tr> </tbody> </table>'''
    regex = Regex()
    d = regex.replaceData(r'(?i)<br/>\s*<br/>', '<br />', text)
    print d